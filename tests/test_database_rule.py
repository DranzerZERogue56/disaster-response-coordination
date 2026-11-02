"""CR-001 / migration 0002: the database itself refuses an assigned unit whose
proposal is not approved, whoever tries to write it."""
import glob
import sqlite3
import subprocess
import sys

import pytest


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "rule.sqlite")
    c.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    yield c
    c.close()


def make_proposal(conn, final_status=None):
    report_id = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
    ).lastrowid
    decided = "2026-11-01T12:00:00+00:00" if final_status else None
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
        "recommended_unit_id, reasoning, alternatives, model_identifier, model_version, "
        "generated_at, final_status, decided_by, decided_at) "
        "VALUES (?, 1, 90, 1, 'r', '[]', 'fake', '1', 't', ?, ?, ?)",
        (report_id, final_status, "auto" if final_status else None, decided),
    ).lastrowid
    conn.commit()
    return pid


def hold(conn, pid, unit_id=1):
    conn.execute(
        "UPDATE units SET status = 'reserved', reserved_by_proposal_id = ?, "
        "reserved_at = 't', released_expected_by = 't' WHERE id = ?",
        (pid, unit_id),
    )
    conn.commit()


def assign(conn, unit_id=1):
    conn.execute("UPDATE units SET status = 'assigned' WHERE id = ?", (unit_id,))
    conn.commit()


@pytest.mark.parametrize("final_status", [None, "rejected", "unresolved_would_escalate"])
def test_cannot_assign_a_unit_whose_proposal_is_not_approved(conn, final_status):
    pid = make_proposal(conn, final_status)
    hold(conn, pid)
    with pytest.raises(sqlite3.IntegrityError, match="can only be assigned"):
        assign(conn)
    assert conn.execute("SELECT status FROM units WHERE id = 1").fetchone()[0] == "reserved"


@pytest.mark.parametrize("final_status", ["approved", "modified"])
def test_can_assign_when_the_proposal_is_approved_or_modified(conn, final_status):
    pid = make_proposal(conn, final_status)
    hold(conn, pid)
    assign(conn)
    assert conn.execute("SELECT status FROM units WHERE id = 1").fetchone()[0] == "assigned"


def test_cannot_insert_a_unit_as_assigned_for_an_undecided_proposal(conn):
    pid = make_proposal(conn)
    with pytest.raises(sqlite3.IntegrityError, match="can only be assigned"):
        conn.execute(
            "INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status, "
            "reserved_by_proposal_id) VALUES (1, 'Medical', 1, 'assigned', ?)",
            (pid,),
        )


def test_cannot_unapprove_a_proposal_while_its_unit_is_assigned(conn):
    pid = make_proposal(conn, "approved")
    hold(conn, pid)
    assign(conn)
    for bad in ("rejected", None):
        with pytest.raises(sqlite3.IntegrityError, match="stop being approved"):
            conn.execute(
                "UPDATE agent_proposals SET final_status = ?, decided_at = ? WHERE id = ?",
                (bad, None if bad is None else "t", pid),
            )


def test_proposal_can_be_changed_once_the_unit_is_freed(conn):
    pid = make_proposal(conn, "approved")
    hold(conn, pid)
    assign(conn)
    conn.execute(
        "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, "
        "reserved_at = NULL, released_expected_by = NULL WHERE id = 1"
    )
    conn.execute("UPDATE agent_proposals SET final_status = 'rejected' WHERE id = ?", (pid,))
    conn.commit()


def test_migration_runner_applies_the_triggers_on_a_fresh_database(tmp_path):
    db = tmp_path / "fresh.sqlite"
    subprocess.run([sys.executable, "tools/migrate.py", str(db)], check=True, capture_output=True)
    c = sqlite3.connect(db)
    names = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
    c.close()
    assert names == {
        "units_assigned_requires_approved_on_insert",
        "units_assigned_requires_approved_on_update",
        "proposals_stay_approved_while_unit_assigned",
    }
