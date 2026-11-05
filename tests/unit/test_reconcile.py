"""Task 6: reconciling two agents' differing pictures of one incident (FR-COORD-02)."""
import glob
import sqlite3
from datetime import UTC, datetime

import pytest

from src.negotiation.reconcile import (
    ReconcileError,
    override_reconciliation,
    reconcile,
    record_version,
)

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "reconcile.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    c.execute("INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (1, 'Fire', 'alive', ?)", (NOW.isoformat(),))
    c.commit()
    yield c
    c.close()


def make_report(conn):
    rid = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at) "
        "VALUES (1, 'x', 'y', 't', 'u', 'created', 't')"
    ).lastrowid
    conn.commit()
    return rid


def versions(conn, report_id):
    return {r["id"]: dict(r) for r in conn.execute("SELECT * FROM incident_versions WHERE report_id = ?", (report_id,))}


def log(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM reconciliation_log ORDER BY id")]


@pytest.mark.covers("FR-COORD-02-AC1")
def test_the_newer_data_becomes_active_and_the_older_is_kept_as_history(conn):
    report = make_report(conn)
    older = record_version(conn, report, 1, {"people": 2}, "2026-11-01T12:00:00+00:00", now=NOW)
    newer = record_version(conn, report, 2, {"people": 5}, "2026-11-01T12:05:00+00:00", now=NOW)

    result = reconcile(conn, report, now=NOW)

    assert result["active_version_id"] == newer and result["changed"] is True
    stored = versions(conn, report)
    assert stored[newer]["active"] == 1 and stored[older]["active"] == 0
    assert stored[older]["superseded_at"] is None or stored[older]["data"] == '{"people": 2}'  # still there, still readable
    assert len(stored) == 2  # nothing deleted
    assert [(e["kind"], e["original_version_id"], e["chosen_version_id"]) for e in log(conn)] == [("automatic", newer, newer)]


@pytest.mark.covers("FR-COORD-02-AC1")
def test_the_order_the_agents_reported_in_does_not_matter_only_the_data_time(conn):
    report = make_report(conn)
    newer = record_version(conn, report, 2, {"people": 5}, "2026-11-01T12:05:00+00:00", now=NOW)  # recorded first
    record_version(conn, report, 1, {"people": 2}, "2026-11-01T12:00:00+00:00", now=NOW)  # an older picture arrives later
    assert reconcile(conn, report, now=NOW)["active_version_id"] == newer


@pytest.mark.covers("FR-COORD-02-AC1")
def test_data_times_in_different_time_zones_are_compared_as_real_moments(conn):
    report = make_report(conn)
    record_version(conn, report, 1, {"v": "a"}, "2026-11-01T12:10:00+00:00", now=NOW)
    later = record_version(conn, report, 2, {"v": "b"}, "2026-11-01T07:30:00-05:00", now=NOW)  # 12:30 UTC
    assert reconcile(conn, report, now=NOW)["active_version_id"] == later


def test_equal_data_times_resolve_deterministically_the_later_recorded_wins(conn):
    report = make_report(conn)
    record_version(conn, report, 1, {"v": "a"}, "2026-11-01T12:00:00+00:00", now=NOW)
    second = record_version(conn, report, 2, {"v": "b"}, "2026-11-01T12:00:00+00:00", now=NOW)
    assert reconcile(conn, report, now=NOW)["active_version_id"] == second
    assert reconcile(conn, report, now=NOW)["active_version_id"] == second  # and it does not flip


def test_reconciling_again_with_nothing_new_changes_nothing_and_logs_nothing(conn):
    report = make_report(conn)
    record_version(conn, report, 1, {"v": 1}, "2026-11-01T12:00:00+00:00", now=NOW)
    reconcile(conn, report, now=NOW)
    again = reconcile(conn, report, now=NOW)
    assert again["changed"] is False and len(log(conn)) == 1


@pytest.mark.covers("FR-COORD-02-AC2")
def test_a_human_override_is_logged_with_who_when_and_the_original_automatic_decision(conn):
    report = make_report(conn)
    older = record_version(conn, report, 1, {"people": 2}, "2026-11-01T12:00:00+00:00", now=NOW)
    newer = record_version(conn, report, 2, {"people": 5}, "2026-11-01T12:05:00+00:00", now=NOW)
    reconcile(conn, report, now=NOW)

    result = override_reconciliation(conn, report, older, "the second agent was reading a stale feed", 1, now=NOW)

    entry = log(conn)[-1]
    assert (entry["kind"], entry["decided_by"], entry["decided_at"]) == ("override", 1, NOW.isoformat())  # who and when
    assert (entry["original_version_id"], entry["chosen_version_id"]) == (newer, older)  # the automatic decision, and the change
    assert entry["reason"] == "the second agent was reading a stale feed"
    assert versions(conn, report)[older]["active"] == 1 and result["active_version_id"] == older


@pytest.mark.covers("FR-COORD-02-AC2")
@pytest.mark.parametrize("reason", [None, "", "   "])
def test_an_override_without_a_reason_is_refused(conn, reason):
    report = make_report(conn)
    older = record_version(conn, report, 1, {"v": 1}, "2026-11-01T12:00:00+00:00", now=NOW)
    record_version(conn, report, 2, {"v": 2}, "2026-11-01T12:05:00+00:00", now=NOW)
    reconcile(conn, report, now=NOW)
    with pytest.raises(ReconcileError) as exc:
        override_reconciliation(conn, report, older, reason, 1, now=NOW)
    assert exc.value.code == "REASON_REQUIRED" and len(log(conn)) == 1


def test_an_observer_cannot_override(conn):
    report = make_report(conn)
    first = record_version(conn, report, 1, {"v": 1}, "2026-11-01T12:00:00+00:00", now=NOW)
    observer = conn.execute(
        "INSERT INTO dispatcher_accounts (username, password_hash, password_salt, role, is_fictional_test_account, created_at) "
        "VALUES ('watcher', 'x', 'x', 'observer', 1, 't')"
    ).lastrowid
    conn.commit()
    with pytest.raises(ReconcileError) as exc:
        override_reconciliation(conn, report, first, "why", observer, now=NOW)
    assert exc.value.code == "NOT_A_DISPATCHER"


def test_a_version_of_another_incident_cannot_be_chosen(conn):
    one, other = make_report(conn), make_report(conn)
    record_version(conn, one, 1, {"v": 1}, "2026-11-01T12:00:00+00:00", now=NOW)
    foreign = record_version(conn, other, 1, {"v": 9}, "2026-11-01T12:00:00+00:00", now=NOW)
    with pytest.raises(ReconcileError) as exc:
        override_reconciliation(conn, one, foreign, "why", 1, now=NOW)
    assert exc.value.code == "VERSION_NOT_FOUND"


def test_a_human_choice_stands_until_newer_data_arrives(conn):
    report = make_report(conn)
    older = record_version(conn, report, 1, {"v": 1}, "2026-11-01T12:00:00+00:00", now=NOW)
    record_version(conn, report, 2, {"v": 2}, "2026-11-01T12:05:00+00:00", now=NOW)
    reconcile(conn, report, now=NOW)
    override_reconciliation(conn, report, older, "stale feed", 1, now=NOW)

    assert reconcile(conn, report, now=NOW)["active_version_id"] == older  # nothing new: the human choice stands

    newest = record_version(conn, report, 1, {"v": 3}, "2026-11-01T12:20:00+00:00", now=NOW)
    assert reconcile(conn, report, now=NOW)["active_version_id"] == newest  # genuinely newer data: automatic again
    assert [e["kind"] for e in log(conn)] == ["automatic", "override", "automatic"]


def test_history_is_never_deleted_by_reconciling(conn):
    report = make_report(conn)
    ids = [record_version(conn, report, 1 + (i % 2), {"v": i}, f"2026-11-01T12:{i:02d}:00+00:00", now=NOW) for i in range(6)]
    for _ in range(3):
        reconcile(conn, report, now=NOW)
    assert set(versions(conn, report)) == set(ids)


def test_what_a_version_says_cannot_be_rewritten_and_the_log_is_append_only(conn):
    report = make_report(conn)
    version = record_version(conn, report, 1, {"v": 1}, "2026-11-01T12:00:00+00:00", now=NOW)
    reconcile(conn, report, now=NOW)
    with pytest.raises(sqlite3.IntegrityError, match="cannot be changed"):
        conn.execute("UPDATE incident_versions SET data = '{}' WHERE id = ?", (version,))
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        conn.execute("UPDATE reconciliation_log SET reason = 'edited'")


def test_unknown_report_and_bad_input_are_refused(conn):
    with pytest.raises(LookupError):
        reconcile(conn, 9999, now=NOW)
    report = make_report(conn)
    with pytest.raises(ValueError):
        record_version(conn, report, 1, {"v": 1}, "not a time", now=NOW)
    with pytest.raises(TypeError):
        record_version(conn, report, 1, "not a dict", "2026-11-01T12:00:00+00:00", now=NOW)
