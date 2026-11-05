"""Task 11: a dispatcher approves a proposal but with a different unit: "modify" (decision D4; FR-AGENT-03-AC2)."""
import sqlite3

import pytest

from src.decide_proposal.service import DecideError, decide_human, stub_dispatcher_id
from src.unit_registry.service import RegistryError, release_expired
from tests.unit.test_human_decision import T0, held_proposal, load_schema_and_seed, row


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "modify.sqlite")
    c.row_factory = sqlite3.Row
    load_schema_and_seed(c)
    yield c
    c.close()


def unit_state(conn, unit_id):
    r = row(conn, "units", unit_id)
    return r["status"], r["reserved_by_proposal_id"]


@pytest.mark.covers("FR-AGENT-03-AC2")
def test_modify_assigns_the_chosen_unit_and_frees_the_original(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    dispatcher = stub_dispatcher_id(conn)

    result = decide_human(conn, pid, "modify", dispatcher, now=T0, modified_unit_id=2)

    assert result["final_status"] == "modified" and result["unit_id"] == 2 and result["released_unit_id"] == 1
    assert result["decided_by"] == str(dispatcher) and result["decided_at"] == T0.isoformat()
    assert unit_state(conn, 2) == ("assigned", pid)
    assert unit_state(conn, 1) == ("available", None)
    stored = row(conn, "agent_proposals", pid)
    assert stored["final_status"] == "modified" and stored["recommended_unit_id"] == 1  # what the agent recommended is kept


@pytest.mark.covers("FR-AGENT-03-AC2")
@pytest.mark.parametrize("missing", [None, True, "2", 2.0])
def test_modify_without_a_real_unit_number_is_refused_and_changes_nothing(conn, missing):
    pid, _ = held_proposal(conn, unit_id=1)
    with pytest.raises(DecideError) as exc:
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=missing)
    assert exc.value.code == "MODIFIED_UNIT_REQUIRED"
    assert row(conn, "agent_proposals", pid)["final_status"] is None and unit_state(conn, 1)[0] == "reserved"


@pytest.mark.covers("FR-AGENT-03-AC2")
def test_modify_to_a_taken_unit_changes_nothing(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    other, _ = held_proposal(conn, unit_id=2)  # unit 2 is reserved by another proposal
    with pytest.raises(RegistryError) as exc:
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=2)
    assert exc.value.code == "UNIT_ALREADY_RESERVED"
    assert row(conn, "agent_proposals", pid)["final_status"] is None
    assert unit_state(conn, 1) == ("reserved", pid) and unit_state(conn, 2) == ("reserved", other)


def test_modify_to_a_unit_that_is_out_of_service_or_unknown_is_refused(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    conn.execute("UPDATE units SET status = 'out_of_service' WHERE id = 2")
    conn.commit()
    with pytest.raises(RegistryError) as exc:
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=2)
    assert exc.value.code == "UNIT_UNAVAILABLE"
    with pytest.raises(RegistryError) as exc:
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=999)
    assert exc.value.code == "UNIT_NOT_FOUND"
    assert row(conn, "agent_proposals", pid)["final_status"] is None


def test_modify_to_a_unit_of_another_scenario_run_is_refused(conn):
    conn.execute("INSERT INTO scenario_runs (mode, scenario_file, team_size_config, started_at) VALUES ('batch', 'x', '{}', 't')")
    conn.execute("INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (2, 'Medical', 'alive', 't')")
    foreign = conn.execute("INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) VALUES (2, 'Medical', 2, 'available')").lastrowid
    conn.commit()
    pid, _ = held_proposal(conn, unit_id=1)
    with pytest.raises(RegistryError) as exc:
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=foreign)
    assert exc.value.code == "UNIT_NOT_FOUND" and row(conn, "agent_proposals", pid)["final_status"] is None


def test_modify_to_the_unit_it_already_holds_is_refused_as_not_a_change(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    with pytest.raises(DecideError) as exc:
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=1)
    assert exc.value.code == "MODIFIED_UNIT_UNCHANGED" and row(conn, "agent_proposals", pid)["final_status"] is None


def test_modify_after_the_four_minute_hold_ran_out_finds_the_proposal_already_rejected_and_assigns_nothing(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    release_expired(conn, now=T0.replace(minute=6))  # the timeout frees unit 1 and rejects the proposal (FR-RES-03)
    result = decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=2)
    assert result["already_decided"] is True and result["final_status"] == "rejected"
    assert unit_state(conn, 2) == ("available", None)  # the late modify did not quietly assign a unit


def test_a_unit_id_given_with_approve_or_reject_is_refused_not_ignored(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    for decision in ("approve", "reject"):
        with pytest.raises(DecideError) as exc:
            decide_human(conn, pid, decision, stub_dispatcher_id(conn), modified_unit_id=2)
        assert exc.value.code == "INVALID_DECISION"
    assert row(conn, "agent_proposals", pid)["final_status"] is None


def test_a_second_modify_returns_the_first_decision_and_moves_nothing(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    decide_human(conn, pid, "modify", stub_dispatcher_id(conn), now=T0, modified_unit_id=2)
    again = decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=1)
    assert again["already_decided"] is True and again["final_status"] == "modified" and unit_state(conn, 2) == ("assigned", pid)


def test_an_observer_cannot_modify(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    observer = conn.execute(
        "INSERT INTO dispatcher_accounts (username, password_hash, password_salt, role, is_fictional_test_account, created_at) "
        "VALUES ('watcher', 'x', 'x', 'observer', 1, 't')"
    ).lastrowid
    conn.commit()
    with pytest.raises(DecideError) as exc:
        decide_human(conn, pid, "modify", observer, modified_unit_id=2)
    assert exc.value.code == "NOT_A_DISPATCHER"


def test_the_database_rule_allows_a_modified_proposal_to_hold_an_assigned_unit(conn):
    pid, _ = held_proposal(conn, unit_id=1)
    decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=2)
    # allowed: the unit is assigned to a 'modified' proposal (migration 0002 accepts approved or modified) ...
    assert unit_state(conn, 2) == ("assigned", pid)
    # ... and the rule still holds the other way: it cannot be turned into a rejection while the unit is assigned
    with pytest.raises(sqlite3.IntegrityError, match="stop being approved"):
        conn.execute("UPDATE agent_proposals SET final_status = 'rejected' WHERE id = ?", (pid,))


def test_a_unit_taken_in_the_gap_between_the_check_and_the_write_leaves_nothing_half_done(conn, monkeypatch):
    pid, _ = held_proposal(conn, unit_id=1)
    import src.decide_proposal.service as svc

    real = svc._take_unit

    def thief(c, unit_id, proposal_id, stamp):
        c.execute("UPDATE units SET status = 'out_of_service' WHERE id = ?", (unit_id,))  # someone got there first
        return real(c, unit_id, proposal_id, stamp)

    monkeypatch.setattr(svc, "_take_unit", thief)
    with pytest.raises(RegistryError):
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn), modified_unit_id=2)
    assert row(conn, "agent_proposals", pid)["final_status"] is None and unit_state(conn, 1) == ("reserved", pid)
