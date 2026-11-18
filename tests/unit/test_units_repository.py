"""The data-access layer for units (pilot, docs/superpowers/plans/2026-11-18-database-options.md).

The repository owns every statement that touches the `units` table and returns plain Python values, so the service
above it does not know which database is underneath. Behaviour is unchanged: the existing registry tests prove that.
"""
import glob
import sqlite3
from pathlib import Path

import pytest

from src.data.units_repo import UnitRepository


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "repo.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        c.executescript(Path(path).read_text(encoding="utf-8"))
    c.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    yield c
    c.close()


def proposal(conn, approved=False):
    rid = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
    ).lastrowid
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, model_identifier, model_version, generated_at) "
        "VALUES (?, 1, 50, 1, 'r', '[]', 'fake', '1', 't')",
        (rid,),
    ).lastrowid
    if approved:
        conn.execute("UPDATE agent_proposals SET final_status = 'approved', decided_by = 'x', decided_at = 't' WHERE id = ?", (pid,))
    conn.commit()
    return pid


def test_all_units_returns_plain_dicts_in_id_order(conn):
    units = UnitRepository(conn).all_units()
    assert [u["id"] for u in units] == [1, 2]
    assert set(units[0]) == {"id", "unit_type", "status", "released_expected_by"}
    assert type(units[0]) is dict and units[0]["status"] == "available"


def test_status_of_a_unit_and_of_one_that_does_not_exist(conn):
    repo = UnitRepository(conn)
    assert repo.status_of(1) == "available" and repo.status_of(999) is None


def test_try_reserve_succeeds_once_and_a_second_caller_is_told_no(conn):
    repo, p1, p2 = UnitRepository(conn), proposal(conn), proposal(conn)
    assert repo.try_reserve(1, p1, "2026-11-01T12:00:00+00:00", "2026-11-01T12:04:00+00:00") is True
    assert repo.try_reserve(1, p2, "2026-11-01T12:00:01+00:00", "2026-11-01T12:04:01+00:00") is False
    assert repo.status_of(1) == "reserved" and repo.reserved_by(p1) == [1] and repo.reserved_by(p2) == []


def test_free_reserved_frees_only_a_reserved_unit(conn):
    repo, pid = UnitRepository(conn), proposal(conn, approved=True)
    repo.try_reserve(1, pid, "t0", "t1")
    assert repo.free_reserved(1) is True and repo.status_of(1) == "available"
    assert repo.free_reserved(1) is False  # nothing to free the second time
    repo.try_reserve(1, pid, "t0", "t1")
    assert repo.try_assign(1, pid) is True
    assert repo.free_reserved(1) is False and repo.status_of(1) == "assigned"  # an assigned unit is never freed by this


def test_expired_reservations_lists_those_whose_window_has_passed(conn):
    repo, p1, p2 = UnitRepository(conn), proposal(conn), proposal(conn)
    repo.try_reserve(1, p1, "2026-11-01T12:00:00+00:00", "2026-11-01T12:04:00+00:00")
    repo.try_reserve(2, p2, "2026-11-01T12:03:00+00:00", "2026-11-01T12:07:00+00:00")
    assert repo.expired_reservations("2026-11-01T12:05:00+00:00") == [(1, p1)]
    assert repo.expired_reservations("2026-11-01T11:00:00+00:00") == []


def test_try_assign_needs_the_same_proposal_to_hold_the_reservation(conn):
    repo, mine, other = UnitRepository(conn), proposal(conn, approved=True), proposal(conn, approved=True)
    repo.try_reserve(1, mine, "t0", "t1")
    assert repo.try_assign(1, other) is False
    assert repo.try_assign(1, mine) is True and repo.assigned_unit_of(mine) == 1
    assert repo.assigned_unit_of(other) is None


def test_moving_an_assignment_uses_release_assigned_and_try_assign_available(conn):
    repo, pid = UnitRepository(conn), proposal(conn, approved=True)
    repo.try_reserve(1, pid, "t0", "t1")
    repo.try_assign(1, pid)
    assert repo.release_assigned(1) is True and repo.status_of(1) == "available"
    assert repo.try_assign_available(2, pid, "2026-11-01T12:10:00+00:00") is True
    assert repo.assigned_unit_of(pid) == 2
    assert repo.try_assign_available(2, pid, "t") is False  # already taken


def test_undecided_holder_is_the_proposal_holding_a_reservation_nobody_has_decided(conn):
    repo, pid = UnitRepository(conn), proposal(conn)
    repo.try_reserve(1, pid, "t0", "t1")
    assert repo.undecided_holder(1) == pid
    conn.execute("UPDATE agent_proposals SET final_status = 'approved', decided_by = 'x', decided_at = 't' WHERE id = ?", (pid,))
    assert repo.undecided_holder(1) is None  # decided: no longer contestable
    assert repo.undecided_holder(2) is None  # not reserved at all


@pytest.mark.parametrize("hostile", ["1; DROP TABLE units; --", "' OR '1'='1", "1 OR 1=1", "\x00", "Robert'); DROP TABLE units;--"])
def test_a_hostile_value_in_any_parameter_is_just_data_and_the_table_survives(conn, hostile):
    repo = UnitRepository(conn)
    assert repo.status_of(hostile) is None
    assert repo.reserved_by(hostile) == [] and repo.assigned_unit_of(hostile) is None
    assert repo.try_reserve(hostile, 1, "t", "t") is False
    assert conn.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 2
