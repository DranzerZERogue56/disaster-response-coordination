"""Slice 7: Override Assignment (FR-RES-02, FR-AUDIT-02)."""
import glob
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.decide_proposal.service import decide_auto, decide_human, stub_dispatcher_id
from src.override_assignment.service import (
    OverrideError,
    add_follow_up,
    override_assignment,
)
from src.unit_registry.service import RegistryError, reserve

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def load_schema_and_seed(c):
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "override.sqlite")
    c.row_factory = sqlite3.Row
    load_schema_and_seed(c)
    yield c
    c.close()


def make_proposal(conn, confidence=90, unit_id=1, generated_at=None):
    report_id = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
    ).lastrowid
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
        "recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at) VALUES (?, 1, ?, ?, 'r', ?, 'fake', '1', ?)",
        (report_id, confidence, unit_id, json.dumps([2]), (generated_at or T0).isoformat()),
    ).lastrowid
    conn.commit()
    reserve(conn, unit_id, pid, now=T0)
    return pid


def auto_assigned(conn):
    pid = make_proposal(conn)
    decide_auto(conn, pid, now=T0 + timedelta(seconds=1))
    return pid


def human_assigned(conn, seconds_to_decide=90):
    pid = make_proposal(conn, confidence=40)
    decide_human(
        conn, pid, "approve", stub_dispatcher_id(conn), now=T0 + timedelta(seconds=seconds_to_decide)
    )
    return pid


def unit_status(conn, unit_id):
    return conn.execute("SELECT status FROM units WHERE id = ?", (unit_id,)).fetchone()[0]


def overrides(conn):
    return conn.execute("SELECT * FROM dispatcher_overrides ORDER BY id").fetchall()


def test_override_moves_the_assignment_and_logs_who_when_why_and_the_original_choice(conn):
    pid = auto_assigned(conn)
    dispatcher = stub_dispatcher_id(conn)
    result = override_assignment(
        conn, pid, 2, "Unit 2 is closer to the scene", dispatcher, now=T0 + timedelta(minutes=2)
    )

    assert result["status"] == "overridden" and result["new_unit_id"] == 2
    assert (unit_status(conn, 1), unit_status(conn, 2)) == ("available", "assigned")
    assert conn.execute("SELECT final_status FROM agent_proposals WHERE id = ?", (pid,)).fetchone()[0] == "modified"

    (row,) = overrides(conn)
    assert row["dispatcher_account_id"] == dispatcher  # who
    assert row["overridden_at"] == (T0 + timedelta(minutes=2)).isoformat()  # when
    assert row["reason"] == "Unit 2 is closer to the scene"  # why
    assert row["original_agent_choice_unit_id"] == 1  # the agent's own choice
    assert row["new_unit_id"] == 2


def test_elapsed_time_from_ai_escalation_to_human_approval_is_recorded(conn):
    pid = human_assigned(conn, seconds_to_decide=90)
    result = override_assignment(conn, pid, 2, "better fit", stub_dispatcher_id(conn), now=T0 + timedelta(minutes=3))

    assert result["elapsed_seconds_escalation_to_approval"] == 90
    assert overrides(conn)[0]["ai_escalated_at"] == T0.isoformat()


def test_an_auto_approved_assignment_has_no_escalation_to_time(conn):
    pid = auto_assigned(conn)
    result = override_assignment(conn, pid, 2, "better fit", stub_dispatcher_id(conn))

    assert result["elapsed_seconds_escalation_to_approval"] is None
    assert overrides(conn)[0]["ai_escalated_at"] is None


@pytest.mark.parametrize("reason", ["", "   ", None])
def test_no_reason_is_rejected_and_nothing_changes(conn, reason):
    pid = auto_assigned(conn)
    with pytest.raises(OverrideError) as exc:
        override_assignment(conn, pid, 2, reason, stub_dispatcher_id(conn))

    assert exc.value.code == "REASON_REQUIRED"
    assert (unit_status(conn, 1), unit_status(conn, 2)) == ("assigned", "available")
    assert overrides(conn) == []


def test_only_a_real_assignment_can_be_overridden(conn):
    held = make_proposal(conn, confidence=40)  # reserved, undecided
    dispatcher = stub_dispatcher_id(conn)
    for pid in (held, 999):
        with pytest.raises(OverrideError) as exc:
            override_assignment(conn, pid, 2, "why", dispatcher)
        assert exc.value.code == "ASSIGNMENT_NOT_FOUND"

    decide_human(conn, held, "reject", dispatcher)
    with pytest.raises(OverrideError) as exc:
        override_assignment(conn, held, 2, "why", dispatcher)
    assert exc.value.code == "ASSIGNMENT_NOT_FOUND"


def test_overriding_to_a_unit_that_is_taken_fails_cleanly_with_no_log_row(conn):
    first = auto_assigned(conn)  # unit 1 assigned
    second = make_proposal(conn, unit_id=2)
    decide_auto(conn, second)  # unit 2 assigned

    with pytest.raises(RegistryError) as exc:
        override_assignment(conn, first, 2, "want unit 2", stub_dispatcher_id(conn))

    assert exc.value.code == "UNIT_ALREADY_RESERVED"
    assert unit_status(conn, 1) == "assigned"  # the original assignment is intact
    assert conn.execute("SELECT final_status FROM agent_proposals WHERE id = ?", (first,)).fetchone()[0] == "approved"
    assert overrides(conn) == []


def test_every_override_is_its_own_log_row_even_to_the_same_unit(conn):
    pid = auto_assigned(conn)
    dispatcher = stub_dispatcher_id(conn)
    override_assignment(conn, pid, 2, "first reason", dispatcher)
    override_assignment(conn, pid, 2, "second reason, same unit", dispatcher)
    override_assignment(conn, pid, 1, "back again", dispatcher)

    rows = overrides(conn)
    assert [r["reason"] for r in rows] == ["first reason", "second reason, same unit", "back again"]
    assert [r["original_agent_choice_unit_id"] for r in rows] == [1, 1, 1]
    assert (unit_status(conn, 1), unit_status(conn, 2)) == ("assigned", "available")


def test_observer_accounts_cannot_override(conn):
    pid = auto_assigned(conn)
    observer = conn.execute(
        "INSERT INTO dispatcher_accounts (username, password_hash, password_salt, role, "
        "is_fictional_test_account, created_at) VALUES ('watcher', 'x', 'x', 'observer', 1, 't')"
    ).lastrowid
    conn.commit()
    with pytest.raises(OverrideError) as exc:
        override_assignment(conn, pid, 2, "why", observer)
    assert exc.value.code == "NOT_A_DISPATCHER"
    assert overrides(conn) == []


def test_follow_up_is_added_to_the_same_entry_without_touching_the_assignment(conn):
    pid = auto_assigned(conn)
    dispatcher = stub_dispatcher_id(conn)
    result = override_assignment(conn, pid, 2, "short reason", dispatcher, now=T0)
    oid = result["override_id"]

    add_follow_up(conn, oid, "Longer explanation: road closed on 4th.", dispatcher, now=T0 + timedelta(hours=3))
    add_follow_up(conn, oid, "Also: unit 1 was low on supplies.", dispatcher, now=T0 + timedelta(days=2))

    (row,) = overrides(conn)  # still one entry
    assert row["reason"] == "short reason"
    assert "road closed on 4th" in row["follow_up_explanation"]
    assert "low on supplies" in row["follow_up_explanation"]
    assert (unit_status(conn, 1), unit_status(conn, 2)) == ("available", "assigned")


def test_follow_up_errors(conn):
    pid = auto_assigned(conn)
    dispatcher = stub_dispatcher_id(conn)
    oid = override_assignment(conn, pid, 2, "reason", dispatcher)["override_id"]
    with pytest.raises(OverrideError) as exc:
        add_follow_up(conn, oid, "  ", dispatcher)
    assert exc.value.code == "FOLLOW_UP_REQUIRED"
    with pytest.raises(OverrideError) as exc:
        add_follow_up(conn, 999, "text", dispatcher)
    assert exc.value.code == "OVERRIDE_NOT_FOUND"


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


def test_override_through_the_routes(client):
    tc, db = client
    a = tc.post(
        "/reports",
        json={
            "location": "4th & Main St",
            "severity_raw": "person fell, visible leg injury, conscious and talking",
            "timestamp_reported": "2026-11-01T12:00:00+00:00",
            "reporting_unit": "field-unit-7",
        },
    ).get_json()
    pid = a["proposal"]["proposal_id"]
    assert a["reservation"]["unit_id"] == 1

    assert tc.post(f"/assignments/{pid}/override", json={"new_unit_id": 2}).status_code == 400  # no reason
    assert tc.post("/assignments/999/override", json={"new_unit_id": 2, "reason": "x"}).status_code == 404

    ok = tc.post(f"/assignments/{pid}/override", json={"new_unit_id": 2, "reason": "unit 2 is closer"})
    assert ok.status_code == 200
    body = ok.get_json()
    assert body["status"] == "overridden"
    assert body["notification"]["unit_id"] == 2  # the unit that now holds it is told

    follow = tc.post(f"/overrides/{body['override_id']}/follow-up", json={"text": "more detail"})
    assert follow.status_code == 200 and "more detail" in follow.get_json()["follow_up_explanation"]
    assert tc.post("/overrides/999/follow-up", json={"text": "x"}).status_code == 404

    c = sqlite3.connect(db)
    assert c.execute("SELECT count(*) FROM notifications").fetchone()[0] == 2  # original + override
    c.close()
