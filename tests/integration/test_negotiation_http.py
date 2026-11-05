"""Task 5, end to end: a higher-severity incident takes a contested unit through the real route."""
import glob
import json
import sqlite3

import pytest

VAGUE = "something happened, not sure how bad, no one is answering"  # Moderate, confidence 40: held for a dispatcher
SEVERE = "man collapsed, chest pain, not breathing well"  # Severe, confidence 95: always held for a dispatcher
CLEAR = "person fell, visible leg injury, conscious and talking"  # Serious, confidence 95: auto-approved


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "negotiation_http.sqlite"
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


def send(client, text, minute):
    body = {
        "location": "4th & Main St",
        "severity_raw": text,
        "timestamp_reported": f"2026-11-01T12:{minute:02d}:00+00:00",
        "reporting_unit": "field-unit-7",
    }
    return client.post("/reports", data=json.dumps(body), content_type="application/json")


def rows(db, sql):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    return out


@pytest.mark.covers("FR-COORD-01-AC1")
def test_a_severe_incident_takes_the_unit_a_moderate_one_was_waiting_on_and_it_is_logged(world):
    client, db = world
    assigned = send(client, CLEAR, 1).get_json()  # takes unit 1 for good
    waiting = send(client, VAGUE, 2).get_json()  # holds unit 2, waiting for a dispatcher
    assert (assigned["reservation"]["unit_id"], waiting["reservation"]["unit_id"]) == (1, 2)

    severe = send(client, SEVERE, 3)  # no unit is free: unit 1 is assigned, unit 2 is only held

    assert severe.status_code == 201
    body = severe.get_json()
    assert body["reservation"]["unit_id"] == 2 and body["reservation"]["won_tiebreak_against"] == waiting["proposal"]["proposal_id"]
    log = rows(db, "SELECT * FROM tiebreak_log")
    assert [(r["winner_proposal_id"], r["loser_proposal_id"], r["reason"], r["protocol_followed"]) for r in log] == [
        (body["proposal"]["proposal_id"], waiting["proposal"]["proposal_id"], "severity", 1)
    ]
    # the moderate incident was not silently dropped: its proposal is history and a human has been asked
    assert rows(db, f"SELECT final_status, decided_by FROM agent_proposals WHERE id = {waiting['proposal']['proposal_id']}") == [
        {"final_status": "rejected", "decided_by": "tiebreak"}
    ]
    escalation = rows(db, "SELECT reason, resolved_at FROM human_escalations")
    assert escalation == [{"reason": "TIEBREAK_LOST_NO_UNIT", "resolved_at": None}]
    pending = [p["proposal_id"] for p in client.get("/proposals/pending").get_json()["pending"]]
    assert pending == [body["proposal"]["proposal_id"]]


def test_a_moderate_incident_cannot_take_a_unit_from_a_severe_one(world):
    client, db = world
    send(client, CLEAR, 1)  # unit 1 assigned
    severe = send(client, SEVERE, 2).get_json()  # holds unit 2, waiting
    late = send(client, VAGUE, 3)  # nothing free, and it would lose the tiebreak

    assert late.status_code == 409 and late.get_json()["error"]["code"] == "UNIT_ALREADY_RESERVED"
    held = rows(db, f"SELECT final_status FROM agent_proposals WHERE id = {severe['proposal']['proposal_id']}")
    assert held == [{"final_status": None}]  # the severe incident still holds its unit
    assert rows(db, "SELECT reason FROM tiebreak_log") == [{"reason": "severity"}]
