"""Resolve Negotiation Conflict (docs/architecture.md section 5), Milestone 11 / FR-COORD-01, FR-COORD-03.

Applies the one tiebreak (src/negotiation/tiebreak.py, ADR 0007) to stored proposals, logs every resolution
in the append-only `tiebreak_log` with both richness scores so a stranger can recompute it, and handles what
follows:

  * A proposal that loses a contested unit is kept as history (final_status 'rejected', decided_by
    'tiebreak'), never deleted, and its incident gets a new proposal for the next best available unit
    (FR-COORD-01-AC2). If no unit is available, the incident goes to a human via `human_escalations`:
    nothing is allowed to disappear silently.
  * Resolving the same pair twice returns the same logged answer (idempotent).
  * A unit that is already assigned is never contestable (the registry never offers it to a tiebreak).

The Unit Registry does not import this module (that would be a cycle); a caller passes `contest` to
`reserve_for_proposal(..., on_conflict=contest)`.
"""
import json
from datetime import UTC, datetime

from src.negotiation.tiebreak import Contender, compare, richness
from src.unit_registry.service import RegistryError, release_for_proposal, reserve

FAR_FUTURE = "9999-12-31T23:59:59+00:00"  # a report time that cannot be read never wins on "reported first"


def _usable_time(text):
    try:
        datetime.fromisoformat(str(text))
        return str(text)
    except ValueError:
        return FAR_FUTURE


def contender_for(conn, proposal_id):
    """The three tiebreak inputs of a stored proposal. Severity comes from the report; richness and the
    reported time from the input data recorded with the proposal (CR-004), or from the report if the
    proposal predates that column."""
    row = conn.execute(
        "SELECT p.input_data, r.severity, r.location, r.severity_raw, r.description, r.timestamp_reported "
        "FROM agent_proposals p JOIN incident_reports r ON r.id = p.report_id WHERE p.id = ?",
        (proposal_id,),
    ).fetchone()
    if row is None:
        raise LookupError(f"No proposal with id {proposal_id}")
    data = json.loads(row["input_data"]) if row["input_data"] else {
        k: row[k] for k in ("location", "severity_raw", "description", "timestamp_reported")
    }
    return Contender(proposal_id, row["severity"] or "Minor", richness(data), _usable_time(data.get("timestamp_reported")))


def _logged(row):
    return {
        "log_id": row["id"],
        "winner": row["winner_proposal_id"],
        "loser": row["loser_proposal_id"],
        "reason": row["reason"],
        "resolved_at": row["resolved_at"],
    }


def resolve_conflict(conn, proposal_a, proposal_b, now=None):
    """Apply the tiebreak to two proposals and log it. Returns {winner, loser, reason, resolved_at, log_id}.
    Raises ValueError for the same proposal twice and LookupError for an unknown one."""
    if proposal_a == proposal_b:
        raise ValueError("a proposal cannot contend with itself")
    low, high = sorted((proposal_a, proposal_b))
    contender_a, contender_b = contender_for(conn, proposal_a), contender_for(conn, proposal_b)
    existing = conn.execute("SELECT * FROM tiebreak_log WHERE pair_low = ? AND pair_high = ?", (low, high)).fetchone()
    if existing:
        return _logged(existing)

    result = compare(contender_a, contender_b)
    by_id = {contender_a.proposal_id: contender_a, contender_b.proposal_id: contender_b}
    stamp = (now or datetime.now(UTC)).isoformat()
    cur = conn.execute(
        "INSERT INTO tiebreak_log (winner_proposal_id, loser_proposal_id, pair_low, pair_high, reason, "
        "winner_richness, loser_richness, protocol_followed, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
        (result.winner, result.loser, low, high, result.reason, by_id[result.winner].richness, by_id[result.loser].richness, stamp),
    )
    conn.commit()
    return {"log_id": cur.lastrowid, "winner": result.winner, "loser": result.loser, "reason": result.reason, "resolved_at": stamp}


def verify_log_entry(conn, log_id):
    """Recompute a logged resolution from the stored proposals; True only if it matches the log exactly."""
    log = conn.execute("SELECT * FROM tiebreak_log WHERE id = ?", (log_id,)).fetchone()
    if log is None:
        return False
    ca, cb = contender_for(conn, log["pair_low"]), contender_for(conn, log["pair_high"])
    result = compare(ca, cb)
    scores = {ca.proposal_id: ca.richness, cb.proposal_id: cb.richness}
    return (
        result.winner == log["winner_proposal_id"]
        and result.loser == log["loser_proposal_id"]
        and result.reason == log["reason"]
        and scores[result.winner] == log["winner_richness"]
        and scores[result.loser] == log["loser_richness"]
        and bool(log["protocol_followed"])
    )


def requeue_loser(conn, loser_proposal_id, contested_unit_id, winner_proposal_id, now=None):
    """Give the losing proposal's incident the next best available unit (FR-COORD-01-AC2): a new proposal for
    the same report, with the original's confidence and reasoning, reserved at once. If no unit is available,
    the incident is put in front of a human (human_escalations)."""
    stamp = (now or datetime.now(UTC)).isoformat()
    old = conn.execute("SELECT * FROM agent_proposals WHERE id = ?", (loser_proposal_id,)).fetchone()
    contested = conn.execute("SELECT unit_type, scenario_run_id FROM units WHERE id = ?", (contested_unit_id,)).fetchone()

    wanted = [u for u in [*json.loads(old["alternatives"]), old["recommended_unit_id"]] if u != contested_unit_id]
    others = [
        r["id"]
        for r in conn.execute(
            "SELECT id FROM units WHERE scenario_run_id = ? AND unit_type = ? AND status = 'available' ORDER BY id",
            (contested["scenario_run_id"], contested["unit_type"]),
        )
    ]
    ordered = list(dict.fromkeys([*wanted, *others]))
    available = {r["id"] for r in conn.execute("SELECT id FROM units WHERE status = 'available'")}
    candidates = [u for u in ordered if u in available and u != contested_unit_id]

    if not candidates:
        conn.execute(
            "INSERT INTO human_escalations (report_id, proposal_id, reason, created_at) VALUES (?, ?, 'TIEBREAK_LOST_NO_UNIT', ?)",
            (old["report_id"], loser_proposal_id, stamp),
        )
        conn.commit()
        return {"requeued": False, "new_proposal_id": None, "reason": "TIEBREAK_LOST_NO_UNIT"}

    chosen, rest = candidates[0], candidates[1:]
    node = conn.execute("SELECT agent_node_id FROM units WHERE id = ?", (chosen,)).fetchone()["agent_node_id"]
    new_id = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, "
        "model_identifier, model_version, generated_at, input_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            old["report_id"],
            node,
            old["confidence"],
            chosen,
            (
                f"Re-proposed after losing the tiebreak for unit {contested_unit_id} to proposal {winner_proposal_id}. "
                f"Original reasoning: {old['reasoning']}"
            ),
            json.dumps(rest),
            old["model_identifier"],
            old["model_version"],
            stamp,
            old["input_data"],
        ),
    ).lastrowid
    conn.commit()
    try:
        reserve(conn, chosen, new_id, now=now)
    except RegistryError:  # the unit was taken between choosing it and reserving it: a person must place this incident
        conn.execute(
            "INSERT INTO human_escalations (report_id, proposal_id, reason, created_at) VALUES (?, ?, 'TIEBREAK_LOST_NO_UNIT', ?)",
            (old["report_id"], new_id, stamp),
        )
        conn.commit()
        return {"requeued": False, "new_proposal_id": new_id, "reason": "TIEBREAK_LOST_NO_UNIT"}
    return {"requeued": True, "new_proposal_id": new_id, "unit_id": chosen}


def contest(conn, challenger_proposal_id, holder_proposal_id, unit_id, now=None):
    """The registry's `on_conflict` hook: `challenger` wants a unit that `holder` has reserved but not yet had
    approved. Resolve it; True if the challenger won and the unit is now free for it, False if it lost."""
    result = resolve_conflict(conn, challenger_proposal_id, holder_proposal_id, now)
    if result["winner"] != challenger_proposal_id:
        return False
    stamp = (now or datetime.now(UTC)).isoformat()
    conn.execute(
        "UPDATE agent_proposals SET final_status = 'rejected', decided_by = 'tiebreak', decided_at = ? "
        "WHERE id = ? AND final_status IS NULL",
        (stamp, holder_proposal_id),
    )
    release_for_proposal(conn, holder_proposal_id)  # commits; the unit is available again
    requeue_loser(conn, holder_proposal_id, unit_id, challenger_proposal_id, now)
    return True
