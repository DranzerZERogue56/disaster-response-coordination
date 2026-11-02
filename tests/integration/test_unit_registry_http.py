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

