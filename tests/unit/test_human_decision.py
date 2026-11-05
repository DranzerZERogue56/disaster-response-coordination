import glob
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.decide_proposal.service import (
    DecideError,
    decide_human,
    list_pending,
    stub_dispatcher_id,
)
from src.unit_registry.service import RegistryError, release_expired, reserve

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def load_schema_and_seed(c):
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "test.sqlite")
    c.row_factory = sqlite3.Row
    load_schema_and_seed(c)
    yield c
    c.close()


def held_proposal(conn, confidence=40, severity="Moderate", unit_id=1):
    report_id = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', ?)",
        (severity,),
    ).lastrowid
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
        "recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at) VALUES (?, 1, ?, ?, 'r', '[]', 'fake', '1', 't')",
        (report_id, confidence, unit_id),
    ).lastrowid
    conn.commit()
    reserve(conn, unit_id, pid, now=T0)
    return pid, report_id


def row(conn, table, row_id):
    return conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()


def test_stub_dispatcher_is_the_seeded_fictional_account(conn):
    dispatcher = row(conn, "dispatcher_accounts", stub_dispatcher_id(conn))
    assert dispatcher["username"] == "demo-dispatcher"
    assert dispatcher["is_fictional_test_account"] == 1


def test_missing_stub_dispatcher_is_a_clear_error(conn):
    conn.execute("DELETE FROM dispatcher_accounts")
    with pytest.raises(DecideError) as exc:
        stub_dispatcher_id(conn)
    assert exc.value.code == "STUB_DISPATCHER_MISSING"


def test_pending_lists_undecided_and_drops_decided(conn):
    pid, _ = held_proposal(conn)
    assert [p["proposal_id"] for p in list_pending(conn)] == [pid]

    decide_human(conn, pid, "approve", stub_dispatcher_id(conn))
    assert list_pending(conn) == []


@pytest.mark.covers("FR-RES-01-AC1")
def test_approve_records_the_dispatcher_not_auto_and_assigns_the_unit(conn):
    pid, _ = held_proposal(conn)
    dispatcher = stub_dispatcher_id(conn)
    result = decide_human(conn, pid, "approve", dispatcher, now=T0)

    assert result["final_status"] == "approved"
    proposal = row(conn, "agent_proposals", pid)
    assert proposal["decided_by"] == str(dispatcher) != "auto"
    assert proposal["decided_at"] == T0.isoformat()
    assert row(conn, "units", 1)["status"] == "assigned"


@pytest.mark.covers("NFR-REL-02-AC1")
def test_reject_frees_the_unit_and_leaves_the_report_for_a_person(conn):
    pid, report_id = held_proposal(conn)
    result = decide_human(conn, pid, "reject", stub_dispatcher_id(conn))

    assert result["final_status"] == "rejected"
    unit = row(conn, "units", 1)
    assert (unit["status"], unit["reserved_by_proposal_id"]) == ("available", None)
    assert row(conn, "incident_reports", report_id)["status"] == "classified"
    assert conn.execute("SELECT count(*) FROM agent_proposals").fetchone()[0] == 1  # no re-proposal


def test_reject_does_not_free_a_unit_held_by_another_proposal(conn):
    first, _ = held_proposal(conn, unit_id=1)
    second, _ = held_proposal(conn, unit_id=2)
    decide_human(conn, first, "reject", stub_dispatcher_id(conn))

    assert row(conn, "units", 1)["status"] == "available"
    assert row(conn, "units", 2)["status"] == "reserved"
    assert row(conn, "units", 2)["reserved_by_proposal_id"] == second


def test_second_decision_changes_nothing(conn):
    pid, _ = held_proposal(conn)
    dispatcher = stub_dispatcher_id(conn)
    first = decide_human(conn, pid, "approve", dispatcher, now=T0)
    second = decide_human(conn, pid, "reject", dispatcher)

    assert second["already_decided"] is True
    assert second["final_status"] == "approved"
    assert second["decided_at"] == first["decided_at"]
    assert row(conn, "units", 1)["status"] == "assigned"


@pytest.mark.covers("FR-RES-03-AC4", "NFR-REL-02-AC1")
def test_a_held_proposal_whose_clock_runs_out_times_out_and_leaves_the_pending_list(conn):
    pid, _ = held_proposal(conn)
    assert [p["proposal_id"] for p in list_pending(conn)] == [pid]

    release_expired(conn, now=T0 + timedelta(minutes=5))

    timed_out = row(conn, "agent_proposals", pid)
    assert (timed_out["final_status"], timed_out["decided_by"]) == ("rejected", "timeout")
    assert row(conn, "units", 1)["status"] == "available"
    assert list_pending(conn) == []


def test_approving_a_timed_out_proposal_changes_nothing(conn):
    pid, _ = held_proposal(conn)
    release_expired(conn, now=T0 + timedelta(minutes=5))

    result = decide_human(conn, pid, "approve", stub_dispatcher_id(conn))

    assert result["already_decided"] is True and result["final_status"] == "rejected"
    assert result["decided_by"] == "timeout"
    assert row(conn, "units", 1)["status"] == "available"  # nothing was dispatched


def test_approve_when_the_unit_was_lost_some_other_way_fails_and_stays_undecided(conn):
    pid, _ = held_proposal(conn)
    conn.execute(
        "UPDATE units SET status = 'out_of_service', reserved_by_proposal_id = NULL, "
        "reserved_at = NULL, released_expected_by = NULL WHERE id = 1"
    )
    conn.commit()

    with pytest.raises(RegistryError) as exc:
        decide_human(conn, pid, "approve", stub_dispatcher_id(conn))

    assert exc.value.code == "UNIT_NO_LONGER_AVAILABLE"
    assert row(conn, "agent_proposals", pid)["final_status"] is None


def test_observer_account_is_refused(conn):
    pid, _ = held_proposal(conn)
    observer = conn.execute(
        "INSERT INTO dispatcher_accounts (username, password_hash, password_salt, role, "
        "is_fictional_test_account, created_at) VALUES ('watcher', 'x', 'x', 'observer', 1, 't')"
    ).lastrowid
    conn.commit()

    with pytest.raises(DecideError) as exc:
        decide_human(conn, pid, "approve", observer)
    assert exc.value.code == "NOT_A_DISPATCHER"
    assert row(conn, "agent_proposals", pid)["final_status"] is None


def test_bad_decision_and_unknown_proposal(conn):
    pid, _ = held_proposal(conn)
    with pytest.raises(DecideError) as exc:
        decide_human(conn, pid, "modify", stub_dispatcher_id(conn))
    assert exc.value.code == "INVALID_DECISION"
    with pytest.raises(DecideError) as exc:
        decide_human(conn, 999, "approve", stub_dispatcher_id(conn))
    assert exc.value.code == "PROPOSAL_NOT_FOUND"

