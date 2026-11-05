"""Task 11, end to end: a dispatcher modifies a held proposal through the real route."""
import glob
import sqlite3

import pytest

VAGUE = "something happened, not sure how bad, no one is answering"  # confidence 40: held for a dispatcher


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "modify_http.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, db_path


def post_report(client, text=VAGUE):
    return client.post(
        "/reports",
        json={
            "location": "4th & Main St",
            "severity_raw": text,
            "timestamp_reported": "2026-11-01T12:00:00+00:00",
            "reporting_unit": "field-unit-7",
        },
    )


def rows(db, sql):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    return out


@pytest.mark.covers("FR-AGENT-03-AC2")
def test_modify_through_the_route_assigns_the_chosen_unit_and_notifies_it_not_the_original(world):
    client, db = world
    held = post_report(client).get_json()
    pid, original = held["proposal"]["proposal_id"], held["reservation"]["unit_id"]
    chosen = 2 if original == 1 else 1

    response = client.post(f"/proposals/{pid}/decision", json={"decision": "modify", "modified_unit_id": chosen})

    body = response.get_json()
    assert response.status_code == 200 and body["final_status"] == "modified" and body["unit_id"] == chosen
    assert body["notification"]["unit_id"] == chosen  # the unit that now holds the job is told, not the one the agent picked
    assert rows(db, f"SELECT status FROM units WHERE id = {chosen}") == [{"status": "assigned"}]
    assert rows(db, f"SELECT status FROM units WHERE id = {original}") == [{"status": "available"}]
    assert rows(db, "SELECT unit_id FROM notifications") == [{"unit_id": chosen}]
    assert client.get("/proposals/pending").get_json()["pending"] == []


@pytest.mark.parametrize(
    ("payload", "status", "code"),
    [
        ({"decision": "modify"}, 400, "MODIFIED_UNIT_REQUIRED"),
        ({"decision": "modify", "modified_unit_id": "2"}, 400, "MODIFIED_UNIT_REQUIRED"),
        ({"decision": "approve", "modified_unit_id": 2}, 400, "INVALID_DECISION"),
        ({"decision": "modify", "modified_unit_id": 999}, 409, "UNIT_NOT_FOUND"),
    ],
)
def test_bad_modify_requests_get_clear_errors_and_change_nothing(world, payload, status, code):
    client, db = world
    pid = post_report(client).get_json()["proposal"]["proposal_id"]
    response = client.post(f"/proposals/{pid}/decision", json=payload)
    assert (response.status_code, response.get_json()["error"]["code"]) == (status, code)
    assert rows(db, f"SELECT final_status FROM agent_proposals WHERE id = {pid}") == [{"final_status": None}]


def test_modify_to_a_unit_another_incident_is_holding_is_a_409_and_both_holds_survive(world):
    client, db = world
    first = post_report(client).get_json()
    second = post_report(client).get_json()  # holds the other unit
    pid = first["proposal"]["proposal_id"]
    taken = second["reservation"]["unit_id"]
    response = client.post(f"/proposals/{pid}/decision", json={"decision": "modify", "modified_unit_id": taken})
    assert (response.status_code, response.get_json()["error"]["code"]) == (409, "UNIT_ALREADY_RESERVED")
    assert {r["status"] for r in rows(db, "SELECT status FROM units WHERE id IN (1, 2)")} == {"reserved"}
