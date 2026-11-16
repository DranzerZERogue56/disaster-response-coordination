"""Purge Job (docs/architecture.md section 5), Milestone 11 / NFR-PRIV-01.

Incident data is hard-deleted 24 hours after receipt. "Hard" matters: NFR-PRIV-01's own test asks for
zero rows when it queries every data store for the seeded report ids, which a soft-delete flag would not
satisfy. Deleted, in foreign-key order: unit-status events and their inboxes, reconciliation log, incident versions, escalations, tiebreak log, follow-ups, overrides, notifications, proposals, reports.

Retention clocks: `received_at` (reports), `generated_at` (proposals), `overridden_at` (overrides),
`added_at` (follow-ups), `sent_at` (notifications). A row whose parent is being purged goes with it even
if its own clock is younger, so no row is ever left pointing at a deleted one.

Never touched: `dispatcher_accounts` (account data, not incident data) and `scenario_runs` (the one
deliberate exception: the final comparison needs every run's score). Units are RESET to available when the
proposal that held them is purged, not deleted: they are the resources, not incident data (CR-009).
Agent nodes hold no incident data and are left alone.

It runs in one transaction. If anything fails, everything is rolled back and PurgeFailed is raised, loudly:
a failed purge is a privacy failure, not an ordinary one, so it is never retried silently.
`now` and `retention_hours` can be overridden so a test does not wait 24 hours.
"""
import sqlite3
import sys
from datetime import UTC, datetime, timedelta

RETENTION_HOURS = 24

EXPIRED_REPORTS = "SELECT id FROM incident_reports WHERE received_at <= :cutoff"
EXPIRED_PROPOSALS = (
    "SELECT id FROM agent_proposals WHERE generated_at <= :cutoff OR report_id IN (" + EXPIRED_REPORTS + ")"
)
EXPIRED_VERSIONS = (
    "SELECT id FROM incident_versions WHERE recorded_at <= :cutoff OR report_id IN (" + EXPIRED_REPORTS + ")"
)
EXPIRED_OVERRIDES = (
    "SELECT id FROM dispatcher_overrides WHERE overridden_at <= :cutoff OR assignment_id IN (" + EXPIRED_PROPOSALS + ")"
)


EXPIRED_EVENTS = (
    "SELECT id FROM unit_events WHERE recorded_at <= :cutoff OR proposal_id IN (" + EXPIRED_PROPOSALS + ")"
)


class PurgeFailed(Exception):
    """The purge could not finish; nothing was changed."""


def purge(conn, now=None, retention_hours=RETENTION_HOURS):
    """Delete incident data older than `retention_hours`. Returns row counts per table."""
    now = now or datetime.now(UTC)
    args = {"cutoff": (now - timedelta(hours=retention_hours)).isoformat()}
    purged = {}
    try:
        reset = conn.execute(
            "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, reserved_at = NULL, "
            "released_expected_by = NULL WHERE status IN ('reserved', 'assigned') "
            "AND reserved_by_proposal_id IN (" + EXPIRED_PROPOSALS + ")",
            args,
        ).rowcount
        # children before parents, each deletion using subqueries that are still intact
        steps = [
            ("agent_inboxes", "event_id IN (" + EXPIRED_EVENTS + ")"),
            ("unit_events", "id IN (" + EXPIRED_EVENTS + ")"),
            (
                "reconciliation_log",
                "decided_at <= :cutoff OR report_id IN ("
                + EXPIRED_REPORTS
                + ") OR original_version_id IN ("
                + EXPIRED_VERSIONS
                + ") OR chosen_version_id IN ("
                + EXPIRED_VERSIONS
                + ")",
            ),
            ("incident_versions", "id IN (" + EXPIRED_VERSIONS + ")"),
            (
                "human_escalations",
                "created_at <= :cutoff OR report_id IN (" + EXPIRED_REPORTS + ") OR proposal_id IN (" + EXPIRED_PROPOSALS + ")",
            ),
            (
                "tiebreak_log",
                "resolved_at <= :cutoff OR winner_proposal_id IN ("
                + EXPIRED_PROPOSALS
                + ") OR loser_proposal_id IN ("
                + EXPIRED_PROPOSALS
                + ")",
            ),
            ("override_follow_ups", "added_at <= :cutoff OR override_id IN (" + EXPIRED_OVERRIDES + ")"),
            ("dispatcher_overrides", "id IN (" + EXPIRED_OVERRIDES + ")"),
            ("notifications", "sent_at <= :cutoff OR assignment_id IN (" + EXPIRED_PROPOSALS + ")"),
            ("agent_proposals", "id IN (" + EXPIRED_PROPOSALS + ")"),
            ("incident_reports", "id IN (" + EXPIRED_REPORTS + ")"),
        ]
        for table, where in steps:
            purged[table] = conn.execute(f"DELETE FROM {table} WHERE {where}", args).rowcount
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise PurgeFailed(f"purge failed and was rolled back: {exc}") from exc
    ordered = {
        t: purged[t]
        for t in (
            "incident_reports",
            "agent_proposals",
            "dispatcher_overrides",
            "override_follow_ups",
            "notifications",
            "tiebreak_log",
            "human_escalations",
            "reconciliation_log",
            "incident_versions",
            "agent_inboxes",
            "unit_events",
        )
    }
    return {"purged": ordered, "reset": {"units": reset}, "run_at": now.isoformat()}


def run_once(conn_factory, log=None):
    """One scheduled purge (DEF-030). Opens its own connection, runs the purge, closes it. A failed purge is reported
    loudly through `log` (stderr by default) and returns None; it never raises, so the timer thread that calls this
    stays alive and tries again at the next interval, and it is never a silent failure."""
    log = log or (lambda message: print(message, file=sys.stderr))
    conn = conn_factory()
    try:
        return purge(conn)
    except PurgeFailed as exc:
        log(f"PURGE FAILED (nothing was deleted, will try again at the next interval): {exc}")
        return None
    finally:
        conn.close()
