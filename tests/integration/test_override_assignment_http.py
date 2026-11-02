"""Slice 7: Override Assignment (FR-RES-02, FR-AUDIT-02)."""


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
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "override.sqlite")
    c.row_factory = sqlite3.Row
    load_schema_and_seed(c)
    yield c
    c.close()


def overrides(conn):
    return conn.execute("SELECT * FROM dispatcher_overrides ORDER BY id").fetchall()


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
    assert follow.status_code == 200
    assert [f["text"] for f in follow.get_json()["follow_ups"]] == ["more detail"]
    assert tc.post("/overrides/999/follow-up", json={"text": "x"}).status_code == 404

    c = sqlite3.connect(db)
    assert c.execute("SELECT count(*) FROM notifications").fetchone()[0] == 2  # original + override
    c.close()

