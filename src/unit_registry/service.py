"""Resource/Unit Registry (docs/architecture.md §4) — Milestone 10, slice 2.

Serves FR-RES-03 (a unit is reserved the moment it is proposed, so nothing
else can claim it) and the 4-minute release rule (NFR-REL-02). Kept apart
from Classify & Propose on purpose: if reservation breaks, this is the one
file to look at. The route calls it directly after a proposal is written.

Slice 3 added assign_unit (FR-RES-01): reserved -> assigned on approval.
Not here yet: the severity tiebreak between two competing proposals (Milestone 12,
FR-COORD-01).
"""
import json
from datetime import UTC, datetime, timedelta

RESERVATION_MINUTES = 4


class RegistryError(Exception):
    """code is UNIT_ALREADY_RESERVED, UNIT_UNAVAILABLE, UNIT_NOT_FOUND,
    UNIT_NO_LONGER_AVAILABLE or PROPOSAL_NOT_FOUND."""

    def __init__(self, code, message, tried=()):
        self.code = code
        self.tried = list(tried)
        super().__init__(message)


def _now():
    return datetime.now(UTC)


def release_expired(conn, now=None):
    """Free every reserved unit whose 4-minute window has passed.

    A proposal still waiting for a person when its unit's clock runs out is
    timed out: final_status 'rejected' with decided_by 'timeout' (FR-RES-03:
    a proposal that times out frees its unit). That also takes it off the
    pending list, so nobody is asked to approve something that can no longer
    be dispatched. Returns the freed unit ids.
    """
    now = now or _now()
    stamp = now.isoformat()
    expired = conn.execute(
        "SELECT id, reserved_by_proposal_id FROM units "
        "WHERE status = 'reserved' AND released_expected_by <= ?",
        (stamp,),
    ).fetchall()
    for unit in expired:
        _free(conn, unit["id"])
        if unit["reserved_by_proposal_id"] is not None:
            conn.execute(
                "UPDATE agent_proposals SET final_status = 'rejected', decided_by = 'timeout', "
                "decided_at = ? WHERE id = ? AND final_status IS NULL",
                (stamp, unit["reserved_by_proposal_id"]),
            )
    conn.commit()
    return [u["id"] for u in expired]


def release_unit(conn, unit_id):
    """Free one unit right away (a rejected proposal will call this)."""
    _free(conn, unit_id)
    conn.commit()


def release_for_proposal(conn, proposal_id, commit=True):
    """Free whatever unit this proposal is holding (a rejection calls this).
    Only touches a unit still reserved by this exact proposal. Pass
    commit=False to make it part of the caller's transaction."""
    ids = [
        r["id"]
        for r in conn.execute(
            "SELECT id FROM units WHERE status = 'reserved' AND reserved_by_proposal_id = ?",
            (proposal_id,),
        ).fetchall()
    ]
    for unit_id in ids:
        _free(conn, unit_id)
    if commit:
        conn.commit()
    return ids


def _free(conn, unit_id):
    conn.execute(
        "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, "
        "reserved_at = NULL, released_expected_by = NULL WHERE id = ? AND status = 'reserved'",
        (unit_id,),
    )


def reserve(conn, unit_id, proposal_id, now=None):
    """Reserve one unit for a proposal, or raise. The single UPDATE only
    matches an available unit, so two callers can never both win."""
    now = now or _now()
    until = (now + timedelta(minutes=RESERVATION_MINUTES)).isoformat()
    cur = conn.execute(
        "UPDATE units SET status = 'reserved', reserved_by_proposal_id = ?, "
        "reserved_at = ?, released_expected_by = ? WHERE id = ? AND status = 'available'",
        (proposal_id, now.isoformat(), until, unit_id),
    )
    if cur.rowcount == 1:
        conn.commit()
        return {"unit_id": unit_id, "reserved_until": until}

    row = conn.execute("SELECT status FROM units WHERE id = ?", (unit_id,)).fetchone()
    if row is None:
        raise RegistryError("UNIT_NOT_FOUND", f"No unit with id {unit_id}", [unit_id])
    if row["status"] in ("reserved", "assigned"):
        raise RegistryError(
            "UNIT_ALREADY_RESERVED", f"Unit {unit_id} is already {row['status']}", [unit_id]
        )
    raise RegistryError("UNIT_UNAVAILABLE", f"Unit {unit_id} is {row['status']}", [unit_id])


def assign_unit(conn, unit_id, proposal_id, commit=True):
    """Turn this proposal's reservation into an assignment (FR-RES-01).

    Pass commit=False when the caller approves the proposal in the same
    transaction: a unit is only ever "assigned" together with its proposal
    being "approved", never one without the other.

    Only works if the unit is still reserved by this same proposal. If the
    window expired and someone else took it, raise UNIT_NO_LONGER_AVAILABLE
    and change nothing.
    """
    cur = conn.execute(
        "UPDATE units SET status = 'assigned', released_expected_by = NULL "
        "WHERE id = ? AND status = 'reserved' AND reserved_by_proposal_id = ?",
        (unit_id, proposal_id),
    )
    if cur.rowcount != 1:
        raise RegistryError(
            "UNIT_NO_LONGER_AVAILABLE",
            f"Unit {unit_id} is no longer reserved for proposal {proposal_id}",
            [unit_id],
        )
    if commit:
        conn.commit()


def unit_clock(conn, now=None):
    """What anyone using the software can see: every unit's status and, for
    a reserved one, exactly when it will be freed and how many seconds are
    left. Frees anything already expired first, so the numbers are current."""
    now = now or _now()
    release_expired(conn, now)
    units = []
    for r in conn.execute(
        "SELECT id, unit_type, status, released_expected_by FROM units ORDER BY id"
    ).fetchall():
        until = r["released_expected_by"] if r["status"] == "reserved" else None
        seconds_left = None
        if until:
            seconds_left = max(0, int((datetime.fromisoformat(until) - now).total_seconds()))
        units.append(
            {
                "unit_id": r["id"],
                "unit_type": r["unit_type"],
                "status": r["status"],
                "frees_at": until,
                "seconds_left": seconds_left,
            }
        )
    return units


def reassign(conn, proposal_id, new_unit_id, now=None, commit=True):
    """Move an assignment from the unit it holds to `new_unit_id` (FR-RES-02).

    The new unit must be available. The old unit goes back to available.
    Pass commit=False to make it part of the caller's transaction. Moving to
    the unit already assigned is allowed and changes nothing.
    """
    now = now or _now()
    current = conn.execute(
        "SELECT id FROM units WHERE reserved_by_proposal_id = ? AND status = 'assigned'",
        (proposal_id,),
    ).fetchone()
    if current is None:
        raise RegistryError(
            "ASSIGNMENT_NOT_FOUND", f"Proposal {proposal_id} has no assigned unit", [new_unit_id]
        )
    if current["id"] == new_unit_id:
        return {"unit_id": new_unit_id, "changed": False}

    target = conn.execute("SELECT status FROM units WHERE id = ?", (new_unit_id,)).fetchone()
    if target is None:
        raise RegistryError("UNIT_NOT_FOUND", f"No unit with id {new_unit_id}", [new_unit_id])
    if target["status"] != "available":
        code = (
            "UNIT_ALREADY_RESERVED"
            if target["status"] in ("reserved", "assigned")
            else "UNIT_UNAVAILABLE"
        )
        raise RegistryError(code, f"Unit {new_unit_id} is {target['status']}", [new_unit_id])

    conn.execute(
        "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, "
        "reserved_at = NULL, released_expected_by = NULL WHERE id = ? AND status = 'assigned'",
        (current["id"],),
    )
    cur = conn.execute(
        "UPDATE units SET status = 'assigned', reserved_by_proposal_id = ?, reserved_at = ?, "
        "released_expected_by = NULL WHERE id = ? AND status = 'available'",
        (proposal_id, now.isoformat(), new_unit_id),
    )
    if cur.rowcount != 1:
        raise RegistryError(
            "UNIT_ALREADY_RESERVED", f"Unit {new_unit_id} was taken first", [new_unit_id]
        )
    if commit:
        conn.commit()
    return {"unit_id": new_unit_id, "changed": True, "released_unit_id": current["id"]}


def reserve_for_proposal(conn, proposal_id, now=None):
    """Reserve the proposal's recommended unit; if it is taken, try each
    alternative in order. When an alternative wins, the proposal is updated
    to point at it. If every unit is taken, raise UNIT_ALREADY_RESERVED."""
    release_expired(conn, now)
    proposal = conn.execute(
        "SELECT recommended_unit_id, alternatives FROM agent_proposals WHERE id = ?",
        (proposal_id,),
    ).fetchone()
    if proposal is None:
        raise RegistryError("PROPOSAL_NOT_FOUND", f"No proposal with id {proposal_id}")

    candidates = [proposal["recommended_unit_id"], *json.loads(proposal["alternatives"])]
    failed = []
    for unit_id in candidates:
        try:
            result = reserve(conn, unit_id, proposal_id, now)
        except RegistryError as exc:
            if exc.code == "UNIT_NOT_FOUND":
                raise
            failed.append(unit_id)
            continue
        if unit_id != proposal["recommended_unit_id"]:
            remaining = [c for c in candidates if c != unit_id and c not in failed]
            conn.execute(
                "UPDATE agent_proposals SET recommended_unit_id = ?, alternatives = ? WHERE id = ?",
                (unit_id, json.dumps(remaining), proposal_id),
            )
            conn.commit()
        result["retried"] = failed
        return result

    raise RegistryError(
        "UNIT_ALREADY_RESERVED",
        f"Every candidate unit is already taken: {failed}",
        failed,
    )
