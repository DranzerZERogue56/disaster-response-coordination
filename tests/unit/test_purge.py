"""Task 3: the purge job (NFR-PRIV-01): incident data is hard-deleted 24 hours after receipt."""
import glob
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.purge.job import PurgeFailed, purge

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)
TABLES = ["incident_reports", "agent_proposals", "dispatcher_overrides", "override_follow_ups", "notifications"]


def stamp(hours_ago, seconds_extra=0):
    return (NOW - timedelta(hours=hours_ago, seconds=seconds_extra)).isoformat()


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "purge.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    yield c
    c.close()


def make_incident(conn, age_hours, unit_id=1, assigned=True, with_audit_trail=True, proposal_age=None):
    """A report, its proposal, (optionally) an assigned unit, an override, a follow-up and a notification."""
    received = stamp(age_hours)
    report_id = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, "
        "reporting_unit, status, received_at, severity) VALUES (1, 'x', 'y', ?, 'u', 'classified', ?, 'Moderate')",
        (received, received),
    ).lastrowid
    generated = stamp(age_hours if proposal_age is None else proposal_age)
    proposal_id = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, "
        "alternatives, model_identifier, model_version, generated_at, final_status, decided_by, decided_at) "
        "VALUES (?, 1, 90, ?, 'r', '[]', 'fake', '1', ?, 'approved', 'auto', ?)",
        (report_id, unit_id, generated, generated),
    ).lastrowid
    if assigned:
        conn.execute(
            "UPDATE units SET status = 'assigned', reserved_by_proposal_id = ?, reserved_at = ? WHERE id = ?",
            (proposal_id, generated, unit_id),
        )
    if with_audit_trail:
        override_id = conn.execute(
            "INSERT INTO dispatcher_overrides (assignment_id, dispatcher_account_id, new_unit_id, "
            "original_agent_choice_unit_id, reason, overridden_at) VALUES (?, 1, 2, ?, 'why', ?)",
            (proposal_id, unit_id, generated),
        ).lastrowid
        conn.execute(
            "INSERT INTO override_follow_ups (override_id, dispatcher_account_id, text, added_at) VALUES (?, 1, 'more', ?)",
            (override_id, generated),
        )
        conn.execute("INSERT INTO notifications (assignment_id, unit_id, sent_at) VALUES (?, ?, ?)", (proposal_id, unit_id, generated))
    conn.commit()
    return report_id, proposal_id


def count(conn, table):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_nothing_newer_than_24_hours_is_deleted(conn):
    make_incident(conn, age_hours=23, assigned=False)
    result = purge(conn, now=NOW)
    assert all(n == 0 for n in result["purged"].values())
    assert [count(conn, t) for t in TABLES] == [1, 1, 1, 1, 1]


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_exactly_24_hours_old_is_purged_and_one_second_younger_is_kept(conn):
    make_incident(conn, age_hours=24, unit_id=1, assigned=False)
    make_incident(conn, age_hours=24, unit_id=2, assigned=False, proposal_age=0)  # report expired, proposal fresh
    keep_report, _ = make_incident(conn, age_hours=23.999, unit_id=1, assigned=False)
    purge(conn, now=NOW)
    assert [r[0] for r in conn.execute("SELECT id FROM incident_reports")] == [keep_report]


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_everything_older_is_deleted_in_foreign_key_order_and_the_unit_is_reset(conn):
    make_incident(conn, age_hours=25)
    result = purge(conn, now=NOW)

    assert [count(conn, t) for t in TABLES] == [0, 0, 0, 0, 0]
    assert result["purged"] == {t: 1 for t in TABLES}
    unit = conn.execute("SELECT status, reserved_by_proposal_id, reserved_at FROM units WHERE id = 1").fetchone()
    assert (unit["status"], unit["reserved_by_proposal_id"], unit["reserved_at"]) == ("available", None, None)
    assert result["reset"] == {"units": 1}
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []  # no row points at a deleted one


def test_dispatcher_accounts_and_scenario_runs_survive(conn):
    make_incident(conn, age_hours=100)
    accounts, runs = count(conn, "dispatcher_accounts"), count(conn, "scenario_runs")
    purge(conn, now=NOW)
    assert (count(conn, "dispatcher_accounts"), count(conn, "scenario_runs")) == (accounts, runs)
    assert accounts >= 1 and runs >= 1


def test_running_the_purge_twice_changes_nothing_the_second_time(conn):
    make_incident(conn, age_hours=30)
    purge(conn, now=NOW)
    again = purge(conn, now=NOW)
    assert all(n == 0 for n in again["purged"].values()) and again["reset"] == {"units": 0}


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_purge_with_the_clock_overridden_does_not_wait_24_hours(conn):
    report_id, _ = make_incident(conn, age_hours=0, assigned=False)  # received "just now"
    assert purge(conn, now=NOW)["purged"]["incident_reports"] == 0
    assert purge(conn, now=NOW + timedelta(hours=24))["purged"]["incident_reports"] == 1
    assert conn.execute("SELECT id FROM incident_reports WHERE id = ?", (report_id,)).fetchone() is None


def test_a_proposal_belonging_to_an_expired_report_goes_with_it(conn):
    make_incident(conn, age_hours=26, proposal_age=1, assigned=False)  # the proposal alone is young
    result = purge(conn, now=NOW)
    assert result["purged"]["incident_reports"] == 1 and result["purged"]["agent_proposals"] == 1
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_a_custom_retention_window_is_honoured(conn):
    make_incident(conn, age_hours=3, assigned=False)
    assert purge(conn, now=NOW, retention_hours=6)["purged"]["incident_reports"] == 0
    assert purge(conn, now=NOW, retention_hours=2)["purged"]["incident_reports"] == 1


def test_a_failed_purge_is_loud_and_leaves_the_data_whole(conn, monkeypatch):
    make_incident(conn, age_hours=30, assigned=False)
    conn.execute("DROP TABLE notifications")  # something is badly wrong with the store
    conn.commit()
    with pytest.raises(PurgeFailed):
        purge(conn, now=NOW)
    assert count(conn, "incident_reports") == 1  # the half-finished purge was rolled back, not left half-done
