"""DEF-026 (proposals consult the agent's view) and DEF-027 (the tiebreak settles two live proposals on one incident)."""
import glob
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.classify_propose.service import classify_and_propose
from src.heartbeat.service import check_nodes, heartbeat
from src.negotiation.service import settle_report_conflict
from src.unit_registry.service import assign_unit, release_for_proposal, reserve

T0 = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)


class Model:
    identifier = "m"
    version = "1"

    def classify(self, report):
        return {"severity": "Moderate", "unit_type": "Medical", "confidence": 60, "reasoning": "r"}


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "def2627.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    c.execute("INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (1, 'Fire', 'alive', ?)", (T0.isoformat(),))
    c.commit()
    yield c
    c.close()


def make_report(conn, status="created", severity=None, text="person fell, leg injury"):
    rid = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, '4th & Main', ?, '2026-11-01T12:00:00+00:00', 'u', ?, 't', ?)",
        (text, status, severity),
    ).lastrowid
    conn.commit()
    return rid


def make_proposal(conn, report_id, unit_id=1, input_text=None):
    data = json.dumps({"location": "4th & Main", "severity_raw": input_text or "x", "timestamp_reported": "2026-11-01T12:00:00+00:00"})
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at, input_data) VALUES (?, 1, 60, ?, 'r', '[]', 'fake', '1', 't', ?)",
        (report_id, unit_id, data),
    ).lastrowid
    conn.commit()
    return pid


# ---- DEF-026 -------------------------------------------------------------------------------------


@pytest.mark.covers("FR-RES-03-AC3")
def test_a_proposal_does_not_start_from_a_unit_the_proposing_agents_view_shows_as_taken(conn):
    """Unit 1 belongs to the Fire agent (node 2); the Medical agent (node 1) is the one proposing. The Medical agent was
    told unit 1 was reserved, then went silent and missed the release: its view still says reserved, though the
    registry says available. The proposal must start from unit 2, which the agent believes is free."""
    conn.execute("UPDATE units SET agent_node_id = 2 WHERE id = 1")
    conn.commit()
    holder = make_proposal(conn, make_report(conn, "classified", "Moderate"), unit_id=1)
    reserve(conn, 1, holder, now=T0)  # delivered to node 1
    conn.execute("UPDATE agent_nodes SET last_heartbeat_at = ? WHERE id = 1", (T0.isoformat(),))
    for other in (2,):
        heartbeat(conn, other, now=T0 + timedelta(seconds=30))
    check_nodes(conn, now=T0 + timedelta(seconds=30))  # node 1 is now silent
    release_for_proposal(conn, holder)  # cached for node 1: it never hears about it
    assert conn.execute("SELECT status FROM units WHERE id = 1").fetchone()[0] == "available"

    result = classify_and_propose(conn, make_report(conn), Model())

    assert result["recommended_unit_id"] == 2
    assert result["alternatives"] == [1]  # still offered, but behind the unit the agent believes is free


def test_with_every_view_healthy_the_choice_is_unchanged(conn):
    result = classify_and_propose(conn, make_report(conn), Model())
    assert result["recommended_unit_id"] == 1 and result["alternatives"] == [2]


# ---- DEF-027 -------------------------------------------------------------------------------------


@pytest.mark.covers("FR-COORD-03-AC1")
def test_two_live_proposals_on_one_incident_are_settled_by_the_same_tiebreak_and_logged(conn):
    report = make_report(conn, "classified", "Moderate")
    poor = make_proposal(conn, report, unit_id=1, input_text="trouble")
    rich = make_proposal(conn, report, unit_id=2, input_text="elderly man collapsed near the bus stop, conscious, bleeding from the head")
    reserve(conn, 1, poor, now=T0)
    reserve(conn, 2, rich, now=T0)

    outcome = settle_report_conflict(conn, report, now=T0)

    assert outcome == [{"winner": rich, "loser": poor, "reason": "richness"}]
    loser = conn.execute("SELECT final_status, decided_by FROM agent_proposals WHERE id = ?", (poor,)).fetchone()
    assert (loser["final_status"], loser["decided_by"]) == ("rejected", "tiebreak")
    assert conn.execute("SELECT status FROM units WHERE id = 1").fetchone()[0] == "available"  # the loser's hold is freed
    assert conn.execute("SELECT final_status FROM agent_proposals WHERE id = ?", (rich,)).fetchone()[0] is None
    logged = conn.execute("SELECT winner_proposal_id, loser_proposal_id, protocol_followed FROM tiebreak_log").fetchall()
    assert [tuple(r) for r in logged] == [(rich, poor, 1)]


def test_a_single_live_proposal_is_left_alone(conn):
    report = make_report(conn, "classified", "Moderate")
    only = make_proposal(conn, report)
    assert settle_report_conflict(conn, report, now=T0) == []
    assert conn.execute("SELECT final_status FROM agent_proposals WHERE id = ?", (only,)).fetchone()[0] is None


def test_a_loser_that_is_already_approved_goes_to_a_person_instead_of_being_unapproved(conn):
    report = make_report(conn, "classified", "Moderate")
    approved = make_proposal(conn, report, unit_id=1, input_text="trouble")
    challenger = make_proposal(conn, report, unit_id=2, input_text="elderly man collapsed near the bus stop, conscious, bleeding from the head")
    reserve(conn, 1, approved, now=T0)
    conn.execute("UPDATE agent_proposals SET final_status = 'approved', decided_by = 'x', decided_at = 't' WHERE id = ?", (approved,))
    assign_unit(conn, 1, approved)

    settle_report_conflict(conn, report, now=T0)
    settle_report_conflict(conn, report, now=T0)  # and again: still one escalation

    assert conn.execute("SELECT final_status FROM agent_proposals WHERE id = ?", (approved,)).fetchone()[0] == "approved"
    escalations = conn.execute("SELECT proposal_id, reason FROM human_escalations").fetchall()
    assert [tuple(r) for r in escalations] == [(approved, "DUPLICATE_PROPOSALS")] or [tuple(r) for r in escalations] == [(challenger, "DUPLICATE_PROPOSALS")]
    assert len(escalations) == 1


def test_classifying_runs_the_settlement_so_a_second_live_proposal_cannot_survive(conn):
    report = make_report(conn)  # status 'created'
    stray = make_proposal(conn, report, unit_id=2, input_text="trouble")  # a stray live proposal already exists
    reserve(conn, 2, stray, now=T0)
    result = classify_and_propose(conn, report, Model())
    live = conn.execute(
        "SELECT id FROM agent_proposals WHERE report_id = ? AND final_status IS NULL", (report,)
    ).fetchall()
    assert len(live) == 1, f"two live proposals on one incident: {[r['id'] for r in live]} (new one {result['proposal_id']})"
