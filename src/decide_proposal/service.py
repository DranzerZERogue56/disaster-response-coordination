"""Decide Proposal, auto-path (docs/architecture.md §5) — Milestone 10, slice 3.

Serves FR-AGENT-03 and NFR-SEC-02: a proposal proceeds on its own only when
confidence is 75 or more AND the incident is not Severe or Critical.
Anything else is left untouched for a human (slice 4). Marking the unit
'assigned' is the Unit Registry's job (FR-RES-01), so this module never
writes to the units table.
"""
from datetime import UTC, datetime

from src.unit_registry.service import assign_unit, release_for_proposal

CONFIDENCE_THRESHOLD = 75
HIGH_SEVERITIES = ("Severe", "Critical")


class DecideError(Exception):
    """code is PROPOSAL_NOT_FOUND, INVALID_DECISION, STUB_DISPATCHER_MISSING
    or NOT_A_DISPATCHER."""

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

    assign_unit(conn, row["recommended_unit_id"], proposal_id)
    decided_at = (now or datetime.now(UTC)).isoformat()
    conn.execute(
        "UPDATE agent_proposals SET final_status = 'approved', decided_by = 'auto', "
        "decided_at = ? WHERE id = ?",
        (decided_at, proposal_id),
    )
    conn.commit()
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


def decide_human(conn, proposal_id, decision, dispatcher_id, now=None):
    """A dispatcher approves or rejects a proposal.

    approve: unit reserved -> assigned (may raise UNIT_NO_LONGER_AVAILABLE,
    in which case nothing is decided). reject: the held unit is freed.
    A second call on a decided proposal returns the existing decision.
    """
    if decision not in ("approve", "reject"):
        raise DecideError("INVALID_DECISION", f"decision must be approve or reject, got {decision!r}")

    account = conn.execute(
        "SELECT role FROM dispatcher_accounts WHERE id = ?", (dispatcher_id,)
    ).fetchone()
    if account is None or account["role"] not in ("dispatcher", "admin"):
        raise DecideError("NOT_A_DISPATCHER", f"Account {dispatcher_id} may not decide proposals")

    row = conn.execute(
        "SELECT recommended_unit_id, final_status, decided_by, decided_at "
        "FROM agent_proposals WHERE id = ?",
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

    if decision == "approve":
        assign_unit(conn, row["recommended_unit_id"], proposal_id)
        final_status = "approved"
    else:
        release_for_proposal(conn, proposal_id)
        final_status = "rejected"

    decided_at = (now or datetime.now(UTC)).isoformat()
    conn.execute(
        "UPDATE agent_proposals SET final_status = ?, decided_by = ?, decided_at = ? WHERE id = ?",
        (final_status, str(dispatcher_id), decided_at, proposal_id),
    )
    conn.commit()
    return {
        "proposal_id": proposal_id,
        "final_status": final_status,
        "decided_by": str(dispatcher_id),
        "decided_at": decided_at,
    }
