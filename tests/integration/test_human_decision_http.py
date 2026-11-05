import glob
import sqlite3

import pytest


def load_schema_and_seed(c):
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())


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


def post_report(client, text):
    return client.post(
        "/reports",
        json={
            "location": "near the old warehouse on 2nd",
            "severity_raw": text,
            "timestamp_reported": "2026-11-01T12:00:00+00:00",
            "reporting_unit": "field-unit-7",
        },
    )


@pytest.mark.covers("FR-AGENT-03-AC2")
def test_demo_escalation_beat_through_the_routes(client):
    vague = post_report(client, "something happened, not sure how bad, no one's answering")
    assert vague.status_code == 201
    body = vague.get_json()
    assert body["proposal"]["confidence"] < 75
    assert body["decision"]["held_for_human"] is True
    pid = body["proposal"]["proposal_id"]

    pending = client.get("/proposals/pending").get_json()["pending"]
    assert [p["proposal_id"] for p in pending] == [pid]

    decided = client.post(f"/proposals/{pid}/decision", json={"decision": "approve"})
    assert decided.status_code == 200
    assert decided.get_json()["final_status"] == "approved"
    assert decided.get_json()["decided_by"] != "auto"
    assert client.get("/proposals/pending").get_json()["pending"] == []


def test_route_errors(client):
    assert client.post("/proposals/999/decision", json={"decision": "approve"}).status_code == 404
    pid = post_report(client, "something happened").get_json()["proposal"]["proposal_id"]
    assert client.post(f"/proposals/{pid}/decision", json={"decision": "modify"}).status_code == 400
    assert client.post(f"/proposals/{pid}/decision", json={}).status_code == 400

