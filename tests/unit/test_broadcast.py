"""Task 14: every agent sees a unit's status change; an update a down node cannot receive is cached and warned about (FR-RES-03)."""
import glob
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.heartbeat.service import check_nodes, heartbeat
from src.unit_registry.broadcast import agent_view, choices
from src.unit_registry.service import assign_unit, release_for_proposal, reserve

T0 = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "broadcast.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    for role in ("Fire", "Security"):  # nodes 2 and 3 are the other agents; node 1 owns the Medical units
        c.execute("INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (1, ?, 'alive', ?)", (role, T0.isoformat()))
    c.commit()
    yield c
    c.close()


def proposal(conn, unit_id=1):
    rid = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
    ).lastrowid
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at) VALUES (?, 1, 50, ?, 'r', '[]', 'fake', '1', 't')",
        (rid, unit_id),
    ).lastrowid
    conn.commit()
    return pid


def approve(conn, pid):
    conn.execute("UPDATE agent_proposals SET final_status = 'approved', decided_by = 'x', decided_at = 't' WHERE id = ?", (pid,))


def events(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM unit_events ORDER BY id")]


def inbox(conn, node_id):
    return [dict(r) for r in conn.execute("SELECT * FROM agent_inboxes WHERE node_id = ? ORDER BY id", (node_id,))]


def take_node_down(conn, node_id):
    conn.execute("UPDATE agent_nodes SET last_heartbeat_at = ? WHERE id = ?", (T0.isoformat(), node_id))
    for other in (1, 2, 3):
        if other != node_id:
            heartbeat(conn, other, now=T0 + timedelta(seconds=30))
    check_nodes(conn, now=T0 + timedelta(seconds=30))
    assert conn.execute("SELECT status FROM agent_nodes WHERE id = ?", (node_id,)).fetchone()[0] == "not_responding"


@pytest.mark.covers("FR-RES-03-AC1")
def test_every_agent_sees_a_status_change(conn):
    pid = proposal(conn)
    assert agent_view(conn, 2)[1] == "available" and agent_view(conn, 3)[1] == "available"

    reserve(conn, 1, pid, now=T0)
    assert agent_view(conn, 2)[1] == "reserved" and agent_view(conn, 3)[1] == "reserved"

    approve(conn, pid)
    assign_unit(conn, 1, pid)
    assert agent_view(conn, 2)[1] == "assigned" and agent_view(conn, 3)[1] == "assigned"
    assert [e["status"] for e in events(conn)] == ["reserved", "assigned"]
    assert agent_view(conn, 2)[2] == "available"  # a unit nobody touched is still shown as free


@pytest.mark.covers("FR-RES-03-AC1")
def test_a_release_is_seen_too_and_the_owning_agent_is_not_sent_its_own_news(conn):
    pid = proposal(conn)
    reserve(conn, 1, pid, now=T0)
    release_for_proposal(conn, pid)
    assert agent_view(conn, 2)[1] == "available" and agent_view(conn, 3)[1] == "available"
    assert inbox(conn, 1) == []  # node 1 owns unit 1: it is the source of the change, not a recipient
    assert len(inbox(conn, 2)) == 2 and len(inbox(conn, 3)) == 2
    assert agent_view(conn, 1)[1] == "available"  # its own units come from the registry itself


@pytest.mark.covers("FR-RES-03-AC2")
def test_an_update_for_a_down_node_is_cached_and_a_warning_is_raised(conn):
    take_node_down(conn, 3)
    pid = proposal(conn)

    reserve(conn, 1, pid, now=T0 + timedelta(seconds=40))

    cached = inbox(conn, 3)
    assert len(cached) == 1 and cached[0]["cached"] == 1 and cached[0]["delivered_at"] is None
    assert agent_view(conn, 3)[1] == "available"  # it has not received the news yet
    assert agent_view(conn, 2)[1] == "reserved"  # the healthy agent did
    warnings = [dict(r) for r in conn.execute("SELECT * FROM node_notices WHERE message LIKE 'Status update%'")]
    assert [(w["audience"], w["to_node_id"]) for w in warnings] == [("agent", 2)]
    assert "unit 1" in warnings[0]["message"] and "node 3" in warnings[0]["message"] and "cached" in warnings[0]["message"]


@pytest.mark.covers("FR-RES-03-AC2")
def test_cached_updates_are_delivered_in_order_when_the_node_responds_again(conn):
    take_node_down(conn, 3)
    pid = proposal(conn)
    reserve(conn, 1, pid, now=T0 + timedelta(seconds=40))
    approve(conn, pid)
    assign_unit(conn, 1, pid)
    assert agent_view(conn, 3)[1] == "available"

    heartbeat(conn, 3, now=T0 + timedelta(seconds=90))

    assert agent_view(conn, 3)[1] == "assigned"  # the latest of the cached updates wins, in event order
    assert all(row["delivered_at"] for row in inbox(conn, 3)) and inbox(conn, 3)[0]["delivered_at"] == (T0 + timedelta(seconds=90)).isoformat()


def test_a_down_node_with_no_alert_row_still_gets_a_cache_and_nothing_crashes(conn):
    conn.execute("UPDATE agent_nodes SET status = 'not_responding' WHERE id = 3")
    conn.commit()
    reserve(conn, 1, proposal(conn), now=T0)
    assert inbox(conn, 3)[0]["cached"] == 1
    assert conn.execute("SELECT COUNT(*) FROM node_notices WHERE message LIKE 'Status update%'").fetchone()[0] == 0  # nothing to hang a warning on


@pytest.mark.covers("FR-RES-03-AC3")
def test_a_reservation_is_timestamped_and_excluded_from_other_agents_choices(conn):
    pid = proposal(conn)
    assert choices(conn, 2) == [1, 2]

    reserve(conn, 1, pid, now=T0)

    event = events(conn)[0]
    assert (event["unit_id"], event["status"], event["proposal_id"], event["at"]) == (1, "reserved", pid, T0.isoformat())  # timestamped
    assert choices(conn, 2) == [2] and choices(conn, 3) == [2]  # the reserved unit is no longer a choice for the others
    assert conn.execute("SELECT reserved_at FROM units WHERE id = 1").fetchone()[0] == T0.isoformat()  # and cached in the registry


@pytest.mark.covers("FR-RES-03-AC3")
def test_a_reservation_by_one_agent_changes_what_another_would_propose(conn):
    """The point of the criterion: agent 2 asks for a unit after agent 1 reserved one and is not offered it."""
    reserve(conn, 1, proposal(conn), now=T0)
    assert 1 not in choices(conn, 3)
    reserve(conn, 2, proposal(conn, unit_id=2), now=T0 + timedelta(seconds=5))
    assert choices(conn, 3) == []


def test_a_change_that_leaves_the_status_alone_publishes_nothing(conn):
    pid = proposal(conn)
    reserve(conn, 1, pid, now=T0)
    before = len(events(conn))
    conn.execute("UPDATE units SET released_expected_by = '2099-01-01T00:00:00+00:00' WHERE id = 1")
    assert len(events(conn)) == before


def test_the_view_never_goes_backwards_when_events_are_delivered_late(conn):
    take_node_down(conn, 3)
    pid = proposal(conn)
    reserve(conn, 1, pid, now=T0 + timedelta(seconds=40))
    release_for_proposal(conn, pid)  # reserved, then released again while node 3 was down
    heartbeat(conn, 3, now=T0 + timedelta(seconds=90))
    assert agent_view(conn, 3)[1] == "available"  # the last thing that happened, not the first thing delivered


def test_the_purge_deletes_old_status_events_and_their_inboxes(conn):
    from src.purge.job import purge

    pid = proposal(conn)
    reserve(conn, 1, pid, now=T0)
    assert events(conn) and inbox(conn, 2)

    result = purge(conn, now=datetime(2100, 1, 1, tzinfo=UTC))

    assert result["purged"]["unit_events"] >= 1 and result["purged"]["agent_inboxes"] >= 2
    assert events(conn) == [] and inbox(conn, 2) == []


def test_a_node_that_has_resumed_receives_updates_at_once_and_no_false_warning_is_raised(conn):
    """Review finding: resumed-but-unconfirmed is not 'cannot receive'."""
    take_node_down(conn, 3)
    heartbeat(conn, 3, now=T0 + timedelta(seconds=50))  # it answers again; a human has not confirmed yet
    reserve(conn, 1, proposal(conn), now=T0 + timedelta(seconds=60))
    row = inbox(conn, 3)[-1]
    assert row["cached"] == 0 and row["delivered_at"] is not None
    assert agent_view(conn, 3)[1] == "reserved"
    assert conn.execute("SELECT COUNT(*) FROM node_notices WHERE message LIKE 'Status update%'").fetchone()[0] == 0


def test_confirming_recovery_leaves_nothing_cached_behind(conn):
    from src.heartbeat.service import confirm_recovery

    take_node_down(conn, 3)
    pid = proposal(conn)
    reserve(conn, 1, pid, now=T0 + timedelta(seconds=40))  # cached while node 3 is silent
    conn.execute("UPDATE node_alerts SET recovered_at = ? WHERE node_id = 3", (T0.isoformat(),))  # resumed without a heartbeat path
    conn.commit()
    confirm_recovery(conn, 3, 1, now=T0 + timedelta(seconds=70))
    assert [r for r in inbox(conn, 3) if r["delivered_at"] is None] == []
    assert agent_view(conn, 3)[1] == "reserved"
