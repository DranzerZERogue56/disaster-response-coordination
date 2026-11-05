"""Regression tests for DEF-013: a dispatcher approves a held proposal after its unit was lost."""
import glob
import json
import sqlite3

import pytest


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "second_path.sqlite"
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


VAGUE = {
    "location": "near the old warehouse on 2nd",
    "severity_raw": "something happened, not sure how bad, no one is answering",
    "timestamp_reported": "2026-11-01T12:05:00+00:00",
    "reporting_unit": "field-unit-7",
}


def lose_unit(db_path, unit_id, new_status="out_of_service"):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE units SET status = ?, reserved_by_proposal_id = NULL, reserved_at = NULL, "
        "released_expected_by = NULL WHERE id = ?",
        (new_status, unit_id),
    )
    conn.commit()
    conn.close()


def assigned(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id FROM units WHERE status = 'assigned'").fetchall()
    conn.close()
    return [r[0] for r in rows]


@pytest.mark.covers("FR-RES-01-AC2")
@pytest.mark.defect("DEF-013")
def test_a_lost_unit_is_replaced_by_an_alternative_when_the_dispatcher_approves(world):
    client, db = world
    held = client.post("/reports", data=json.dumps(VAGUE), content_type="application/json").get_json()
    lose_unit(db, held["reservation"]["unit_id"])

    resp = client.post(f"/proposals/{held['proposal']['proposal_id']}/decision", json={"decision": "approve"})

    assert resp.status_code == 200 and resp.get_json()["retried_after_unit_loss"] is True
    other = 2 if held["reservation"]["unit_id"] == 1 else 1
    assert assigned(db) == [other]


@pytest.mark.covers("FR-RES-01-AC2")
@pytest.mark.defect("DEF-013")
def test_if_every_unit_is_lost_the_dispatcher_gets_the_error_and_nothing_is_dispatched(world):
    client, db = world
    held = client.post("/reports", data=json.dumps(VAGUE), content_type="application/json").get_json()
    lose_unit(db, 1)
    lose_unit(db, 2)

    resp = client.post(f"/proposals/{held['proposal']['proposal_id']}/decision", json={"decision": "approve"})

    assert resp.status_code == 409
    assert assigned(db) == []


def test_rejecting_does_not_trigger_the_second_path(world):
    client, db = world
    held = client.post("/reports", data=json.dumps(VAGUE), content_type="application/json").get_json()
    resp = client.post(f"/proposals/{held['proposal']['proposal_id']}/decision", json={"decision": "reject"})
    assert resp.status_code == 200 and assigned(db) == []
