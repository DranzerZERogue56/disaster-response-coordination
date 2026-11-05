"""Task 10, end to end: a report arrives while the models are down; the dispatcher still hears about it."""
import glob
import json
import sqlite3

import pytest

from src.classify_propose.chain import ModelChain
from tests.unit.test_model_chain import Model, Sleeper, dies


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "chain_http.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()
    import src.web_ui.app as web

    app = web.create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, db_path, web, monkeypatch


def send(client):
    body = {
        "location": "4th & Main St",
        "severity_raw": "person fell, visible leg injury, conscious and talking",
        "timestamp_reported": "2026-11-01T12:00:00+00:00",
        "reporting_unit": "field-unit-7",
    }
    return client.post("/reports", data=json.dumps(body), content_type="application/json")


def rows(db, sql):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    return out


@pytest.mark.covers("FR-DEGRADE-02-AC1")
def test_with_the_primary_down_a_report_is_still_classified_by_the_next_tier(world):
    client, db, web, patch = world
    patch.setattr(web, "build_chain", lambda: ModelChain(dies("primary"), Model("smaller"), Model("rules"), sleep=Sleeper()))

    response = send(client)

    assert response.status_code == 201 and response.get_json()["proposal"]["confidence"] == 90
    assert rows(db, "SELECT model_identifier FROM agent_proposals") == [{"model_identifier": "smaller"}]


@pytest.mark.covers("FR-DEGRADE-02-AC2")
def test_with_every_model_down_the_report_goes_to_a_human_and_the_reply_says_so(world):
    client, db, web, patch = world
    sleeper = Sleeper()
    patch.setattr(web, "build_chain", lambda: ModelChain(dies("primary"), dies("smaller"), dies("rules"), sleep=sleeper))

    response = send(client)

    body = response.get_json()
    assert response.status_code == 201 and body["proposal"] is None
    assert body["needs_human"]["code"] == "MODEL_CHAIN_EXHAUSTED"
    assert sleeper.sleeps == [10.0] * 6
    assert rows(db, "SELECT reason, resolved_at FROM human_escalations") == [{"reason": "MODEL_CHAIN_EXHAUSTED", "resolved_at": None}]
    assert rows(db, "SELECT status FROM incident_reports") == [{"status": "created"}]  # kept, not lost
