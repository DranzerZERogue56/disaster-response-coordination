"""Decide Proposal, auto-path (docs/architecture.md §5) — Milestone 10, slice 3.

Serves FR-AGENT-03 and NFR-SEC-02: a proposal proceeds on its own only when
confidence is 75 or more AND the incident is not Severe or Critical.
Anything else is left untouched for a human (slice 4). Marking the unit
'assigned' is the Unit Registry's job (FR-RES-01), so this module never
writes to the units table.
"""
from datetime import UTC, datetime

from src.unit_registry.service import RegistryError, assign_unit, release_for_proposal

CONFIDENCE_THRESHOLD = 75
HIGH_SEVERITIES = ("Severe", "Critical")


class DecideError(Exception):
    """code is PROPOSAL_NOT_FOUND, INVALID_DECISION, STUB_DISPATCHER_MISSING,
    NOT_A_DISPATCHER, MODIFIED_UNIT_REQUIRED or MODIFIED_UNIT_UNCHANGED."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def needs_human(confidence, severity):
    """The safety rule. Kept as its own function so it is tested on its own."""
    return confidence < CONFIDENCE_THRESHOLD or severity in HIGH_SEVERITIES


def decide_auto(conn, proposal_id, now=None):
    """Approve the proposal automatically if the rule allows it.

    Returns {"proposal_id", "final_status", "decided_by", "decided_at"} when
    decided, or {"proposal_id", "final_status": None, "held_for_human": True}
    when the rule says a person must decide. A second call on a decided
    proposal returns the existing decision unchanged. If the reserved unit
    was lost in the meantime, RegistryError UNIT_NO_LONGER_AVAILABLE is
    raised and the proposal stays undecided.

    A unit can be lost between reserving and this call only if: (1) its
    4-minute window ran out and the clock freed it, (2) a dispatcher
    rejected the same proposal at that moment, (3) the unit was taken out of
    service (future heartbeat code, FR-DEGRADE-01), or (4) someone edited
    the database by hand. The route calls this immediately after reserving
    and retries once, so the window is a few milliseconds.
    """
    row = conn.execute(
        """
        SELECT p.confidence, p.recommended_unit_id, p.final_status, p.decided_by,
               p.decided_at, r.severity
        FROM agent_proposals p JOIN incident_reports r ON r.id = p.report_id
        WHERE p.id = ?
        """,
        (proposal_id,),
    ).fetchone()
    if row is None:
        raise LookupError(f"No proposal with id {proposal_id}")

    if row["final_status"] is not None:
        return {
            "proposal_id": proposal_id,
            "final_status": row["final_status"],
            "decided_by": row["decided_by"],
            "decided_at": row["decided_at"],
            "already_decided": True,
        }

    if needs_human(row["confidence"], row["severity"]):
        return {"proposal_id": proposal_id, "final_status": None, "held_for_human": True}

    decided_at = (now or datetime.now(UTC)).isoformat()
    # One transaction: the unit becomes "assigned" and the proposal becomes
    # "approved" together or not at all (self-review 3.2).
    try:
        # Approve first, then assign: migration 0002 refuses to assign a unit
        # whose proposal is not yet approved.
        conn.execute(
            "UPDATE agent_proposals SET final_status = 'approved', decided_by = 'auto', "
            "decided_at = ? WHERE id = ?",
            (decided_at, proposal_id),
        )
        assign_unit(conn, row["recommended_unit_id"], proposal_id, commit=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {
        "proposal_id": proposal_id,
        "final_status": "approved",
        "decided_by": "auto",
        "decided_at": decided_at,
    }


# --- Slice 4: the human decision ------------------------------------------
# Real dispatcher login (FR-AUTH-01) does not exist yet. Until it does, the
# one seeded fictional dispatcher account stands in for "the dispatcher".
# Replacing this lookup is the only change real login should need.


def stub_dispatcher_id(conn):
    row = conn.execute(
        "SELECT id FROM dispatcher_accounts "
        "WHERE role = 'dispatcher' AND is_fictional_test_account = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if row is None:
        raise DecideError(
            "STUB_DISPATCHER_MISSING",
            "No fictional dispatcher account found; apply seed/iteration-1.sql",
        )
    return row["id"]


def list_pending(conn):
    """Proposals nobody has decided yet (the ones slice 3 held)."""
    rows = conn.execute(
        """
        SELECT p.id AS proposal_id, p.confidence, p.recommended_unit_id, p.reasoning,
               r.id AS report_id, r.location, r.severity
        FROM agent_proposals p JOIN incident_reports r ON r.id = p.report_id
        WHERE p.final_status IS NULL ORDER BY p.id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def _take_unit(conn, unit_id, proposal_id, stamp):
    """Assign an available unit straight to a proposal (the modify action). The single UPDATE only matches
    an available unit, so a unit taken in the meantime is refused and the caller rolls everything back."""
    cur = conn.execute(
        "UPDATE units SET status = 'assigned', reserved_by_proposal_id = ?, reserved_at = ?, "
        "released_expected_by = NULL WHERE id = ? AND status = 'available'",
        (proposal_id, stamp, unit_id),
    )
    if cur.rowcount != 1:
        raise RegistryError("UNIT_ALREADY_RESERVED", f"Unit {unit_id} was taken first", [unit_id])


def _check_modify_target(conn, unit_id, scenario_run_id, recommended_unit_id):
    if unit_id == recommended_unit_id:
        raise DecideError("MODIFIED_UNIT_UNCHANGED", f"Unit {unit_id} is the unit already proposed; approve instead")
    target = conn.execute("SELECT status, scenario_run_id FROM units WHERE id = ?", (unit_id,)).fetchone()
    if target is None or target["scenario_run_id"] != scenario_run_id:
        raise RegistryError("UNIT_NOT_FOUND", f"No unit with id {unit_id} in this scenario run", [unit_id])
    if target["status"] != "available":
        code = "UNIT_ALREADY_RESERVED" if target["status"] in ("reserved", "assigned") else "UNIT_UNAVAILABLE"
        raise RegistryError(code, f"Unit {unit_id} is {target['status']}", [unit_id])


def decide_human(conn, proposal_id, decision, dispatcher_id, now=None, modified_unit_id=None):
    """A dispatcher approves, modifies or rejects a proposal.

    approve: unit reserved -> assigned (may raise UNIT_NO_LONGER_AVAILABLE,
    in which case nothing is decided). reject: the held unit is freed.
    modify: approve, but with a different, available unit (`modified_unit_id`, required): final_status
    'modified', the held unit is freed and the chosen one assigned in one transaction.
    A second call on a decided proposal returns the existing decision.
    """
    if decision not in ("approve", "reject", "modify"):
        raise DecideError("INVALID_DECISION", f"decision must be approve, modify or reject, got {decision!r}")
    if decision == "modify":
        if type(modified_unit_id) is not int:
            raise DecideError("MODIFIED_UNIT_REQUIRED", "modify needs modified_unit_id, the number of the unit to send instead")
    elif modified_unit_id is not None:
        raise DecideError("INVALID_DECISION", "modified_unit_id only goes with the modify decision")

    account = conn.execute(
        "SELECT role FROM dispatcher_accounts WHERE id = ?", (dispatcher_id,)
    ).fetchone()
    if account is None or account["role"] not in ("dispatcher", "admin"):
        raise DecideError("NOT_A_DISPATCHER", f"Account {dispatcher_id} may not decide proposals")

    row = conn.execute(
        "SELECT p.recommended_unit_id, p.final_status, p.decided_by, p.decided_at, r.scenario_run_id "
        "FROM agent_proposals p JOIN incident_reports r ON r.id = p.report_id WHERE p.id = ?",
        (proposal_id,),
    ).fetchone()
    if row is None:
        raise DecideError("PROPOSAL_NOT_FOUND", f"No proposal with id {proposal_id}")
    if row["final_status"] is not None:
        return {
            "proposal_id": proposal_id,
            "final_status": row["final_status"],
            "decided_by": row["decided_by"],
            "decided_at": row["decided_at"],
            "already_decided": True,
        }
    if decision == "modify":
        _check_modify_target(conn, modified_unit_id, row["scenario_run_id"], row["recommended_unit_id"])

    decided_at = (now or datetime.now(UTC)).isoformat()
    final_status = {"approve": "approved", "reject": "rejected", "modify": "modified"}[decision]
    released = []
    # One transaction, same rule as the auto-path: unit change and decision
    # are saved together or not at all.
    try:
        conn.execute(
            "UPDATE agent_proposals SET final_status = ?, decided_by = ?, decided_at = ? "
            "WHERE id = ?",
            (final_status, str(dispatcher_id), decided_at, proposal_id),
        )
        if decision == "approve":
            assign_unit(conn, row["recommended_unit_id"], proposal_id, commit=False)
        elif decision == "modify":
            released = release_for_proposal(conn, proposal_id, commit=False)
            _take_unit(conn, modified_unit_id, proposal_id, decided_at)
        else:
            release_for_proposal(conn, proposal_id, commit=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    result = {
        "proposal_id": proposal_id,
        "final_status": final_status,
        "decided_by": str(dispatcher_id),
        "decided_at": decided_at,
    }
    if decision == "modify":
        result["unit_id"] = modified_unit_id
        result["released_unit_id"] = released[0] if released else None
    return result
