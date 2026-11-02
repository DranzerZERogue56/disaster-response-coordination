"""Override Assignment (docs/architecture.md section 5) — Milestone 10, slice 7.

Serves FR-RES-02 (and FR-AUDIT-02): a dispatcher can replace any assignment
with a different unit at any time, but only with a reason, and the override
is logged: who, when, why, the agent's original choice, and how long the human
took after the AI asked for approval. After the override takes effect the
dispatcher may keep adding to the same log entry (follow-up), with no time
limit and without blocking the override itself.

Unit status changes belong to the Unit Registry (`reassign`); this module
logs the decision. Everything happens in one transaction, so a failed
override changes nothing and writes no log row. Not built: logging an
observer's blocked attempt (FR-AUTH-01 login does not exist yet).
"""
from datetime import UTC, datetime

from src.unit_registry.service import reassign


class OverrideError(Exception):
    """code is REASON_REQUIRED, ASSIGNMENT_NOT_FOUND, NOT_A_DISPATCHER,
    OVERRIDE_NOT_FOUND or FOLLOW_UP_REQUIRED."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _check_dispatcher(conn, dispatcher_id):
    account = conn.execute(
        "SELECT role FROM dispatcher_accounts WHERE id = ?", (dispatcher_id,)
    ).fetchone()
    if account is None or account["role"] not in ("dispatcher", "admin"):
        raise OverrideError("NOT_A_DISPATCHER", f"Account {dispatcher_id} may not override")


def _seconds_between(start, end):
    try:
        return round((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())
    except (TypeError, ValueError):
        return None


def override_assignment(conn, proposal_id, new_unit_id, reason, dispatcher_id, now=None):
    """Replace the unit assigned to `proposal_id` with `new_unit_id`.

    Raises OverrideError (REASON_REQUIRED, ASSIGNMENT_NOT_FOUND,
    NOT_A_DISPATCHER) or RegistryError (the new unit is not free). On any
    error nothing is changed and nothing is logged.
    """
    if not reason or not str(reason).strip():
        raise OverrideError("REASON_REQUIRED", "An override needs a reason; none was given")
    _check_dispatcher(conn, dispatcher_id)

    proposal = conn.execute(
        "SELECT recommended_unit_id, final_status, decided_by, decided_at, generated_at "
        "FROM agent_proposals WHERE id = ?",
        (proposal_id,),
    ).fetchone()
    if proposal is None or proposal["final_status"] not in ("approved", "modified"):
        raise OverrideError(
            "ASSIGNMENT_NOT_FOUND", f"Proposal {proposal_id} has no assignment to override"
        )

    # A proposal a person decided was escalated to a person by the AI; one the
    # system approved on its own was not, so there is nothing to time.
    escalated = proposal["decided_by"] != "auto"
    ai_escalated_at = proposal["generated_at"] if escalated else None
    elapsed = _seconds_between(proposal["generated_at"], proposal["decided_at"]) if escalated else None

    overridden_at = (now or datetime.now(UTC)).isoformat()
    try:
        reassign(conn, proposal_id, new_unit_id, now=now, commit=False)
        conn.execute(
            "UPDATE agent_proposals SET final_status = 'modified' WHERE id = ?", (proposal_id,)
        )
        cur = conn.execute(
            """
            INSERT INTO dispatcher_overrides
                (assignment_id, dispatcher_account_id, new_unit_id,
                 original_agent_choice_unit_id, reason, ai_escalated_at, overridden_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                dispatcher_id,
                new_unit_id,
                proposal["recommended_unit_id"],
                str(reason).strip(),
                ai_escalated_at,
                overridden_at,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {
        "assignment_id": proposal_id,
        "override_id": cur.lastrowid,
        "status": "overridden",
        "logged_at": overridden_at,
        "new_unit_id": new_unit_id,
        "original_agent_choice_unit_id": proposal["recommended_unit_id"],
        "elapsed_seconds_escalation_to_approval": elapsed,
        "follow_up_open": True,
    }


def add_follow_up(conn, override_id, text, dispatcher_id, now=None):
    """Add to the same log entry. No time limit; never touches the assignment."""
    _check_dispatcher(conn, dispatcher_id)
    if not text or not str(text).strip():
        raise OverrideError("FOLLOW_UP_REQUIRED", "A follow-up needs some text")
    row = conn.execute(
        "SELECT follow_up_explanation FROM dispatcher_overrides WHERE id = ?", (override_id,)
    ).fetchone()
    if row is None:
        raise OverrideError("OVERRIDE_NOT_FOUND", f"No override with id {override_id}")

    stamp = (now or datetime.now(UTC)).isoformat()
    entry = f"[{stamp}] {str(text).strip()}"
    combined = entry if not row["follow_up_explanation"] else row["follow_up_explanation"] + "\n" + entry
    conn.execute(
        "UPDATE dispatcher_overrides SET follow_up_explanation = ? WHERE id = ?",
        (combined, override_id),
    )
    conn.commit()
    return {"override_id": override_id, "follow_up_explanation": combined}
