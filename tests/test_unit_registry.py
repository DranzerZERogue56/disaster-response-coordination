import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.unit_registry.service import (
    RegistryError,
    release_expired,
    release_unit,
    reserve,
    reserve_for_proposal,
)

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def load_schema_and_seed(c):
    with open("migrations/0001-initial.sql", encoding="utf-8") as f:
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


def make_proposal(conn, recommended=1, alternatives=(2,)):
    cur = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Serious')"
    )
    report_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
        "recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at) VALUES (?, 1, 90, ?, 'r', ?, 'fake', '1', 't')",
        (report_id, recommended, json.dumps(list(alternatives))),
    )
    conn.commit()
    return cur.lastrowid


def unit(conn, unit_id):
    return conn.execute("SELECT * FROM units WHERE id = ?", (unit_id,)).fetchone()


def test_reserve_marks_unit_reserved_with_four_minute_window(conn):
    pid = make_proposal(conn)
    result = reserve(conn, 1, pid, now=T0)

    row = unit(conn, 1)
    assert row["status"] == "reserved"
    assert row["reserved_by_proposal_id"] == pid
    assert row["released_expected_by"] == (T0 + timedelta(minutes=4)).isoformat()
    assert result["reserved_until"] == row["released_expected_by"]


def test_reserving_a_reserved_unit_raises_unit_already_reserved(conn):
    first = make_proposal(conn)
    reserve(conn, 1, first, now=T0)
    with pytest.raises(RegistryError) as exc:
        reserve(conn, 1, make_proposal(conn), now=T0)
    assert exc.value.code == "UNIT_ALREADY_RESERVED"
    assert unit(conn, 1)["reserved_by_proposal_id"] == first  # first claim untouched


def test_out_of_service_unit_is_unavailable_not_reserved(conn):
    conn.execute("UPDATE units SET status = 'out_of_service' WHERE id = 1")
    with pytest.raises(RegistryError) as exc:
        reserve(conn, 1, make_proposal(conn))
    assert exc.value.code == "UNIT_UNAVAILABLE"


def test_missing_unit(conn):
    with pytest.raises(RegistryError) as exc:
        reserve(conn, 99, make_proposal(conn))
    assert exc.value.code == "UNIT_NOT_FOUND"


def test_retry_falls_back_to_alternative_and_updates_proposal(conn):
    reserve(conn, 1, make_proposal(conn), now=T0)
    pid = make_proposal(conn, recommended=1, alternatives=(2,))
    result = reserve_for_proposal(conn, pid, now=T0)

    assert result["unit_id"] == 2
    assert result["retried"] == [1]
    row = conn.execute(
        "SELECT recommended_unit_id, alternatives FROM agent_proposals WHERE id = ?", (pid,)
    ).fetchone()
    assert row["recommended_unit_id"] == 2
    assert json.loads(row["alternatives"]) == []


def test_every_unit_taken_raises_and_lists_what_was_tried(conn):
    reserve(conn, 1, make_proposal(conn), now=T0)
    reserve(conn, 2, make_proposal(conn), now=T0)
    with pytest.raises(RegistryError) as exc:
        reserve_for_proposal(conn, make_proposal(conn), now=T0)
    assert exc.value.code == "UNIT_ALREADY_RESERVED"
    assert exc.value.tried == [1, 2]


def test_reservation_frees_itself_after_four_minutes(conn):
    reserve(conn, 1, make_proposal(conn), now=T0)

    assert release_expired(conn, now=T0 + timedelta(minutes=3, seconds=59)) == []
    assert unit(conn, 1)["status"] == "reserved"

    assert release_expired(conn, now=T0 + timedelta(minutes=4)) == [1]
    row = unit(conn, 1)
    assert (row["status"], row["reserved_by_proposal_id"], row["reserved_at"]) == (
        "available",
        None,
        None,
    )


def test_expired_unit_can_be_reserved_again_through_the_proposal_path(conn):
    reserve(conn, 1, make_proposal(conn), now=T0)
    reserve(conn, 2, make_proposal(conn), now=T0)
    later = T0 + timedelta(minutes=5)
    result = reserve_for_proposal(conn, make_proposal(conn), now=later)
    assert result["unit_id"] == 1


def test_release_unit_frees_immediately(conn):
    reserve(conn, 1, make_proposal(conn), now=T0)
    release_unit(conn, 1)
    assert unit(conn, 1)["status"] == "available"


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
        yield tc


def post(client, text):
    return client.post(
        "/reports",
        json={
            "location": "somewhere",
            "severity_raw": text,
            "timestamp_reported": "2026-11-01T12:00:00+00:00",
            "reporting_unit": "u",
        },
    )


def test_route_reserves_then_retries_then_returns_409_when_none_left(client):
    a = post(client, "person fell, visible leg injury, conscious and talking")
    assert a.status_code == 201
    assert a.get_json()["reservation"]["unit_id"] == 1
    assert a.get_json()["decision"]["final_status"] == "approved"  # Serious, 95: auto

    c = post(client, "man collapsed, chest pain, not breathing well")
    assert c.status_code == 201
    assert c.get_json()["reservation"]["unit_id"] == 2
    assert c.get_json()["decision"]["held_for_human"] is True  # Severe: never auto

    d = post(client, "another fall with injury")
    assert d.status_code == 409
    assert d.get_json()["error"]["code"] == "UNIT_ALREADY_RESERVED"
