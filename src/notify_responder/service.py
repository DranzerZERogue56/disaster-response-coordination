"""Notify Responder (docs/architecture.md §5) — Milestone 10, slice 5.

Serves FR-ALERT-01: once an assignment is final, tell the assigned unit.

In this release "tell" means writing a row to `notifications` with
`sent_at` set. No message leaves the machine, because the requirement
names no channel (architecture open question OQ-2). A real channel would
replace the one INSERT below. `acknowledged_at` stays NULL; acknowledgment
is FR-ALERT-02 (Should priority), not built.

Per the architecture contract, notifying the same assignment twice makes
two rows on purpose, so a dispatcher can see a double notification.
"""
from datetime import UTC, datetime


class NotifyError(Exception):
    """code is NOT_ASSIGNED."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def notify_responder(conn, proposal_id, unit_id, now=None):
    """Record a notification for `unit_id`, but only if that unit is really
    assigned to this approved proposal. Nothing is sent for an assignment
    that is not final."""
    row = conn.execute(
        """
        SELECT u.status AS unit_status, u.reserved_by_proposal_id, p.final_status
        FROM units u, agent_proposals p
        WHERE u.id = ? AND p.id = ?
        """,
        (unit_id, proposal_id),
    ).fetchone()
    if (
        row is None
        or row["final_status"] not in ("approved", "modified")
        or row["unit_status"] != "assigned"
        or row["reserved_by_proposal_id"] != proposal_id
    ):
        raise NotifyError(
            "NOT_ASSIGNED",
            f"Unit {unit_id} is not assigned to an approved proposal {proposal_id}",
        )

    sent_at = (now or datetime.now(UTC)).isoformat()
    cur = conn.execute(
        "INSERT INTO notifications (assignment_id, unit_id, sent_at) VALUES (?, ?, ?)",
        (proposal_id, unit_id, sent_at),
    )
    conn.commit()
    return {"notification_id": cur.lastrowid, "unit_id": unit_id, "sent_at": sent_at}


def notify_for_decision(conn, decision):
    """Convenience for the routes: notify the unit behind a fresh approval.
    Returns None when there is nothing to notify (held, rejected, or a
    repeat of an earlier decision)."""
    if decision.get("final_status") not in ("approved", "modified") or decision.get(
        "already_decided"
    ):
        return None
    unit_id = conn.execute(
        "SELECT recommended_unit_id FROM agent_proposals WHERE id = ?",
        (decision["proposal_id"],),
    ).fetchone()["recommended_unit_id"]
    return notify_responder(conn, decision["proposal_id"], unit_id)
