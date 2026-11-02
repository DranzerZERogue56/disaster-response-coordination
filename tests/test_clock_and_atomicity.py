import glob
import sqlite3
import time
from datetime import UTC, datetime, timedelta

import pytest

from src.decide_proposal.service import decide_auto, decide_human, stub_dispatcher_id
from src.unit_registry.service import reserve, unit_clock

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


def reserved_proposal(conn, confidence=90, severity="Moderate", unit_id=1, now=T0):
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
    reserve(conn, unit_id, pid, now=now)
    return pid


def unit(conn, unit_id=1):
    return conn.execute("SELECT * FROM units WHERE id = ?", (unit_id,)).fetchone()


def proposal(conn, pid):
    return conn.execute("SELECT * FROM agent_proposals WHERE id = ?", (pid,)).fetchone()


def assigned_without_approval(conn):
    """The invariant: this must always be empty. A unit is 'assigned' only
    while the proposal that holds it is 'approved'."""
    return conn.execute(
        "SELECT u.id FROM units u LEFT JOIN agent_proposals p "
        "ON p.id = u.reserved_by_proposal_id "
        "WHERE u.status = 'assigned' AND (p.final_status IS NOT 'approved')"
    ).fetchall()


# --- the clock people can see ------------------------------------------------


def test_clock_shows_when_a_reserved_unit_will_be_freed(conn):
    reserved_proposal(conn)

    at_start = {u["unit_id"]: u for u in unit_clock(conn, now=T0)}
    assert at_start[1]["status"] == "reserved"
    assert at_start[1]["frees_at"] == (T0 + timedelta(minutes=4)).isoformat()
    assert at_start[1]["seconds_left"] == 240
    assert at_start[2]["status"] == "available"
    assert at_start[2]["seconds_left"] is None

    later = {u["unit_id"]: u for u in unit_clock(conn, now=T0 + timedelta(seconds=100))}
    assert later[1]["seconds_left"] == 140

    expired = {u["unit_id"]: u for u in unit_clock(conn, now=T0 + timedelta(minutes=4))}
    assert expired[1]["status"] == "available"  # the clock freed it
    assert expired[1]["frees_at"] is None


def test_sweeper_frees_an_expired_reservation_with_nobody_asking(tmp_path, monkeypatch):
    db_path = tmp_path / "sweep.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    load_schema_and_seed(c)
    reserved_proposal(c, now=datetime.now(UTC) - timedelta(minutes=10))
    assert unit(c)["status"] == "reserved"

    from src.web_ui.app import start_sweeper

    start_sweeper(0.05)
    deadline = time.time() + 3
    while time.time() < deadline and unit(c)["status"] != "available":
        time.sleep(0.05)
    assert unit(c)["status"] == "available"
    c.close()


# --- assigned always means approved -----------------------------------------


@pytest.fixture
def block_proposal_updates(conn):
    """Make saving the decision fail, to prove the unit change is undone too."""
    conn.executescript(
        "CREATE TRIGGER no_proposal_update BEFORE UPDATE ON agent_proposals "
        "BEGIN SELECT RAISE(ABORT, 'simulated crash while saving the decision'); END;"
    )


def test_auto_approve_failing_midway_does_not_leave_an_assigned_unit(conn, block_proposal_updates):
    pid = reserved_proposal(conn)
    with pytest.raises(sqlite3.DatabaseError):
        decide_auto(conn, pid)

    assert unit(conn)["status"] == "reserved"
    assert proposal(conn, pid)["final_status"] is None
    assert assigned_without_approval(conn) == []


def test_human_approve_failing_midway_does_not_leave_an_assigned_unit(conn, block_proposal_updates):
    pid = reserved_proposal(conn, confidence=40)
    with pytest.raises(sqlite3.DatabaseError):
        decide_human(conn, pid, "approve", stub_dispatcher_id(conn))

    assert unit(conn)["status"] == "reserved"
    assert assigned_without_approval(conn) == []


def test_human_reject_failing_midway_keeps_the_unit_held(conn, block_proposal_updates):
    pid = reserved_proposal(conn, confidence=40)
    with pytest.raises(sqlite3.DatabaseError):
        decide_human(conn, pid, "reject", stub_dispatcher_id(conn))

    assert unit(conn)["status"] == "reserved"  # not freed while the proposal is still open
    assert proposal(conn, pid)["final_status"] is None


def test_invariant_holds_after_every_normal_path(conn):
    approved = reserved_proposal(conn, unit_id=1)
    decide_auto(conn, approved)
    held = reserved_proposal(conn, confidence=40, unit_id=2)
    decide_auto(conn, held)  # held for a human: unit stays reserved
    assert assigned_without_approval(conn) == []

    decide_human(conn, held, "approve", stub_dispatcher_id(conn))
    assert assigned_without_approval(conn) == []
    assert {u["status"] for u in conn.execute("SELECT status FROM units")} == {"assigned"}


# --- losing the unit between reserving and approving ------------------------


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "route.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    c = sqlite3.connect(db_path)
    load_schema_and_seed(c)
    c.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = True
    with app.test_client() as tc:
        yield tc, db_path


def post_report(client, text="person fell, visible leg injury, conscious and talking"):
    return client.post(
        "/reports",
        json={
            "location": "4th & Main St",
            "severity_raw": text,
            "timestamp_reported": "2026-11-01T12:00:00+00:00",
            "reporting_unit": "field-unit-7",
        },
    )


def lose_the_unit(db_path, proposal_id):
    """Simulate any of the ways a unit can vanish in the gap."""
    c = sqlite3.connect(db_path)
    c.execute(
        "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, "
        "reserved_at = NULL, released_expected_by = NULL WHERE id IN "
        "(SELECT recommended_unit_id FROM agent_proposals WHERE id = ?)",
        (proposal_id,),
    )
    c.commit()
    c.close()


def test_unit_lost_once_is_fixed_automatically(client, monkeypatch):
    tc, db_path = client
    import src.web_ui.app as appmod

    real = appmod.decide_auto
    calls = []

    def lose_first_time(conn, pid):
        calls.append(pid)
        if len(calls) == 1:
            lose_the_unit(db_path, pid)
        return real(conn, pid)

    monkeypatch.setattr(appmod, "decide_auto", lose_first_time)
    resp = post_report(tc)

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["retried_after_unit_loss"] is True
    assert body["decision"]["final_status"] == "approved"
    assert body["notification"]["unit_id"] == body["reservation"]["unit_id"]


def test_unit_lost_twice_gets_its_own_error_code_and_dispatches_nothing(client, monkeypatch):
    tc, db_path = client
    import src.web_ui.app as appmod

    real = appmod.decide_auto

    def always_lose(conn, pid):
        lose_the_unit(db_path, pid)
        return real(conn, pid)

    monkeypatch.setattr(appmod, "decide_auto", always_lose)
    resp = post_report(tc)

    assert resp.status_code == 409
    body = resp.get_json()
    assert body["error"]["code"] == "UNIT_LOST_BEFORE_APPROVAL"
    assert body["error"]["underlying"] == "UNIT_NO_LONGER_AVAILABLE"
    assert body["reservation"] is not None  # the reservation that did succeed is still shown
    c = sqlite3.connect(db_path)
    assert c.execute("SELECT count(*) FROM units WHERE status = 'assigned'").fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM notifications").fetchone()[0] == 0
    c.close()


def test_units_route_and_page_show_the_clock(client):
    tc, _ = client
    post_report(tc, "something happened, not sure how bad")  # held, so its unit stays reserved

    units = tc.get("/units").get_json()["units"]
    held = [u for u in units if u["status"] == "reserved"]
    assert len(held) == 1
    assert 0 < held[0]["seconds_left"] <= 240
    assert held[0]["frees_at"]

    page = tc.get("/reports").get_data(as_text=True)
    assert "Seconds left" in page and "reserved" in page
