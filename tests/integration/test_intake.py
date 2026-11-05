import glob
import sqlite3

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))

    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.close()

    from src.web_ui.app import create_app

    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


@pytest.mark.covers("FR-INTAKE-01-AC1")
def test_submit_and_list_report_round_trip(client):
    resp = client.post(
        "/reports",
        json={
            "location": "123 Test St",
            "severity_raw": "fire visible",
            "timestamp_reported": "2026-10-25T00:00:00+00:00",
            "reporting_unit": "unit-skeleton-1",
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "created"
    assert "report_id" in body

    page = client.get("/reports")
    assert page.status_code == 200
    assert b"123 Test St" in page.data


@pytest.mark.covers("FR-INTAKE-02-AC2")
def test_submit_report_missing_field_rejected(client):
    resp = client.post("/reports", json={"location": "123 Test St"})
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "FIELD_MISSING"

