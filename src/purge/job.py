"""Purge Job (docs/architecture.md section 5), Milestone 11 / NFR-PRIV-01.

Incident data is hard-deleted 24 hours after receipt. "Hard" matters: NFR-PRIV-01's own test asks for
zero rows when it queries every data store for the seeded report ids, which a soft-delete flag would not
satisfy. Deleted, in foreign-key order: follow-ups, overrides, notifications, proposals, reports.

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
from datetime import UTC, datetime, timedelta

RETENTION_HOURS = 24

EXPIRED_REPORTS = "SELECT id FROM incident_reports WHERE received_at <= :cutoff"
EXPIRED_PROPOSALS = (
    "SELECT id FROM agent_proposals WHERE generated_at <= :cutoff OR report_id IN (" + EXPIRED_REPORTS + ")"
)
EXPIRED_OVERRIDES = (
    "SELECT id FROM dispatcher_overrides WHERE overridden_at <= :cutoff OR assignment_id IN (" + EXPIRED_PROPOSALS + ")"
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
    ordered = {t: purged[t] for t in ("incident_reports", "agent_proposals", "dispatcher_overrides", "override_follow_ups", "notifications")}
    return {"purged": ordered, "reset": {"units": reset}, "run_at": now.isoformat()}
