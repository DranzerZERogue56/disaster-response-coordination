"""Task 8: noticing a node that stopped responding, telling the others and a human, and recovery (FR-DEGRADE-01)."""
import glob
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.heartbeat.service import (
    HeartbeatError,
    check_nodes,
    confirm_recovery,
    heartbeat,
)

T0 = datetime(2026, 11, 6, 12, 0, 0, tzinfo=UTC)


def at(seconds):
    return T0 + timedelta(seconds=seconds)


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "heartbeat.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    # the seed has node 1; add 2 and 3 so there are others to tell
    for role in ("Fire", "Security"):
        c.execute("INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (1, ?, 'alive', ?)", (role, T0.isoformat()))
    c.execute("UPDATE agent_nodes SET last_heartbeat_at = ?", (T0.isoformat(),))
    c.commit()
    yield c
    c.close()


def node(conn, node_id):
    return dict(conn.execute("SELECT * FROM agent_nodes WHERE id = ?", (node_id,)).fetchone())


def alerts(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM node_alerts ORDER BY id")]


def notices(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM node_notices ORDER BY id")]


def keep_others_alive(conn, seconds, except_node):
    for n in (1, 2, 3):
        if n != except_node:
            heartbeat(conn, n, now=at(seconds))


@pytest.mark.covers("FR-DEGRADE-01-AC1")
def test_a_node_silent_for_thirty_seconds_is_flagged_and_other_agents_and_a_human_are_notified(conn):
    keep_others_alive(conn, 30, except_node=2)

    flagged = check_nodes(conn, now=at(30))

    assert [f["node_id"] for f in flagged] == [2]
    assert node(conn, 2)["status"] == "not_responding"
    assert node(conn, 1)["status"] == node(conn, 3)["status"] == "alive"
    assert len(alerts(conn)) == 1 and alerts(conn)[0]["node_id"] == 2 and alerts(conn)[0]["raised_at"] == at(30).isoformat()
    sent = notices(conn)
    assert sorted((n["audience"], n["to_node_id"]) for n in sent if n["audience"] == "agent") == [("agent", 1), ("agent", 3)]
    assert [n for n in sent if n["audience"] == "human"] and all(n["alert_id"] == alerts(conn)[0]["id"] for n in sent)


@pytest.mark.covers("FR-DEGRADE-01-AC1")
def test_a_node_silent_for_twenty_nine_seconds_is_not_flagged(conn):
    keep_others_alive(conn, 29, except_node=2)
    assert check_nodes(conn, now=at(29)) == []
    assert node(conn, 2)["status"] == "alive" and alerts(conn) == [] and notices(conn) == []


def test_the_threshold_comes_from_the_interval_and_the_misses(conn):
    keep_others_alive(conn, 19, except_node=2)
    assert check_nodes(conn, now=at(19), interval_s=5, misses=4) == []  # the limit is 5 x 4 = 20 s
    keep_others_alive(conn, 20, except_node=2)
    assert [f["node_id"] for f in check_nodes(conn, now=at(20), interval_s=5, misses=4)] == [2]
    assert node(conn, 2)["status"] == "not_responding"


def test_a_second_poll_does_not_raise_a_second_alert(conn):
    keep_others_alive(conn, 40, except_node=2)
    check_nodes(conn, now=at(30))
    second = check_nodes(conn, now=at(40))
    assert second == [] and len(alerts(conn)) == 1 and len(notices(conn)) == 3  # 2 agents + 1 human, once


def test_a_node_that_never_missed_never_alerts(conn):
    for second in range(0, 120, 10):
        for n in (1, 2, 3):
            heartbeat(conn, n, now=at(second))
        assert check_nodes(conn, now=at(second)) == []
    assert alerts(conn) == [] and notices(conn) == []


def test_a_dead_node_is_not_told_about_itself_or_about_other_dead_nodes(conn):
    heartbeat(conn, 1, now=at(30))  # nodes 2 and 3 are both silent
    flagged = check_nodes(conn, now=at(30))
    assert sorted(f["node_id"] for f in flagged) == [2, 3]
    agent_targets = [(n["alert_id"], n["to_node_id"]) for n in notices(conn) if n["audience"] == "agent"]
    assert all(target == 1 for _alert, target in agent_targets) and len(agent_targets) == 2  # only node 1 is told, once per alert


@pytest.mark.covers("FR-DEGRADE-01-AC2")
def test_a_node_that_resumes_gets_its_alert_marked_as_a_late_recovery(conn):
    keep_others_alive(conn, 30, except_node=2)
    check_nodes(conn, now=at(30))

    result = heartbeat(conn, 2, now=at(75))

    assert result["resumed_after_alert"] is True
    alert = alerts(conn)[0]
    assert alert["recovered_at"] == at(75).isoformat()
    assert all(n["late_recovery"] == 1 and n["updated_at"] == at(75).isoformat() for n in notices(conn))  # earlier notices updated
    assert node(conn, 2)["status"] == "not_responding"  # still not trusted: a human has to check


@pytest.mark.covers("FR-DEGRADE-01-AC2")
def test_the_node_is_only_recovered_after_a_human_confirms(conn):
    keep_others_alive(conn, 30, except_node=2)
    check_nodes(conn, now=at(30))
    heartbeat(conn, 2, now=at(75))
    for _ in range(3):
        check_nodes(conn, now=at(80))  # polling never turns it into 'recovered'
        assert node(conn, 2)["status"] == "not_responding"

    result = confirm_recovery(conn, 2, 1, now=at(90))  # dispatcher 1 is the seeded stand-in

    assert result["status"] == "recovered"
    assert node(conn, 2)["status"] == "recovered" and node(conn, 2)["recovered_confirmed_by"] == 1
    alert = alerts(conn)[0]
    assert (alert["confirmed_by"], alert["confirmed_at"]) == (1, at(90).isoformat())


def test_recovery_cannot_be_confirmed_for_a_node_that_has_not_resumed(conn):
    keep_others_alive(conn, 30, except_node=2)
    check_nodes(conn, now=at(30))
    with pytest.raises(HeartbeatError) as exc:
        confirm_recovery(conn, 2, 1, now=at(40))
    assert exc.value.code == "NODE_NOT_RESUMED" and node(conn, 2)["status"] == "not_responding"


def test_recovery_cannot_be_confirmed_for_a_node_that_never_failed(conn):
    with pytest.raises(HeartbeatError) as exc:
        confirm_recovery(conn, 1, 1, now=at(5))
    assert exc.value.code == "NODE_NOT_FLAGGED"


def test_an_observer_cannot_confirm_a_recovery(conn):
    keep_others_alive(conn, 30, except_node=2)
    check_nodes(conn, now=at(30))
    heartbeat(conn, 2, now=at(50))
    observer = conn.execute(
        "INSERT INTO dispatcher_accounts (username, password_hash, password_salt, role, is_fictional_test_account, created_at) "
        "VALUES ('watcher', 'x', 'x', 'observer', 1, 't')"
    ).lastrowid
    conn.commit()
    with pytest.raises(HeartbeatError) as exc:
        confirm_recovery(conn, 2, observer, now=at(60))
    assert exc.value.code == "NOT_A_DISPATCHER" and node(conn, 2)["status"] == "not_responding"


def test_the_database_itself_refuses_recovered_without_a_human(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE agent_nodes SET status = 'recovered' WHERE id = 2")


def test_a_node_that_resumed_and_then_went_silent_again_raises_a_new_alert(conn):
    keep_others_alive(conn, 30, except_node=2)
    check_nodes(conn, now=at(30))
    heartbeat(conn, 2, now=at(50))  # resumed, awaiting a human
    keep_others_alive(conn, 90, except_node=2)

    flagged = check_nodes(conn, now=at(90))  # silent again for 40 s

    assert [f["node_id"] for f in flagged] == [2] and len(alerts(conn)) == 2
    assert alerts(conn)[1]["recovered_at"] is None


def test_a_recovered_node_can_fail_again_and_is_flagged_again(conn):
    keep_others_alive(conn, 30, except_node=2)
    check_nodes(conn, now=at(30))
    heartbeat(conn, 2, now=at(50))
    confirm_recovery(conn, 2, 1, now=at(55))
    for n in (1, 2, 3):
        heartbeat(conn, n, now=at(60))
    keep_others_alive(conn, 100, except_node=2)
    assert [f["node_id"] for f in check_nodes(conn, now=at(100))] == [2]


def test_a_heartbeat_from_an_unknown_node_is_refused(conn):
    with pytest.raises(LookupError):
        heartbeat(conn, 999, now=at(1))


def test_a_late_stale_heartbeat_does_not_move_the_clock_backwards(conn):
    heartbeat(conn, 1, now=at(50))
    heartbeat(conn, 1, now=at(10))
    assert node(conn, 1)["last_heartbeat_at"] == at(50).isoformat()


@pytest.mark.parametrize(("interval", "misses"), [(0, 3), (-1, 3), (10, 0), (10, -2)])
def test_nonsense_thresholds_are_refused(conn, interval, misses):
    with pytest.raises(ValueError):
        check_nodes(conn, now=at(30), interval_s=interval, misses=misses)
