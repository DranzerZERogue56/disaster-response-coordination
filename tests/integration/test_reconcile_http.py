"""Task 6, end to end: the override route, the log in the real database, and the purge."""
import glob
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.negotiation.reconcile import reconcile, record_version
from src.purge.job import purge

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "reconcile_http.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.execute(
        "INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (1, 'Fire', 'alive', ?)",
        (NOW.isoformat(),),
    )
    report = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at) "
        "VALUES (1, 'x', 'y', 't', 'u', 'created', ?)",
        (NOW.isoformat(),),
    ).lastrowid
    conn.commit()
    older = record_version(conn, report, 1, {"people": 2}, "2026-11-01T12:00:00+00:00", now=NOW)
    newer = record_version(conn, report, 2, {"people": 5}, "2026-11-01T12:05:00+00:00", now=NOW)
    reconcile(conn, report, now=NOW)
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, conn, report, older, newer
    conn.close()


@pytest.mark.covers("FR-COORD-02-AC2")
def test_a_dispatcher_overrides_through_the_route_and_it_is_logged(world):
    client, conn, report, older, newer = world

    response = client.post(
        f"/reconciliations/{report}/override",
        data=json.dumps({"version_id": older, "reason": "second agent read a stale feed"}),
        content_type="application/json",
    )

    assert response.status_code == 200 and response.get_json()["active_version_id"] == older
    entry = dict(conn.execute("SELECT * FROM reconciliation_log ORDER BY id DESC LIMIT 1").fetchone())
    assert (entry["kind"], entry["original_version_id"], entry["chosen_version_id"]) == ("override", newer, older)
    assert entry["decided_by"] is not None and entry["decided_at"] and entry["reason"] == "second agent read a stale feed"


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ({"version_id": 1, "reason": ""}, 400, "REASON_REQUIRED"),
        ({"reason": "why"}, 400, "VERSION_REQUIRED"),
        ({"version_id": "1", "reason": "why"}, 400, "VERSION_REQUIRED"),
        ({"version_id": True, "reason": "why"}, 400, "VERSION_REQUIRED"),
        ({"version_id": 99999, "reason": "why"}, 404, "VERSION_NOT_FOUND"),
        ([1, 2], 400, "VERSION_REQUIRED"),
    ],
)
def test_bad_override_requests_get_clear_errors_and_log_nothing(world, body, status, code):
    client, conn, report, *_ = world
    before = conn.execute("SELECT COUNT(*) FROM reconciliation_log").fetchone()[0]
    response = client.post(f"/reconciliations/{report}/override", data=json.dumps(body), content_type="application/json")
    assert (response.status_code, response.get_json()["error"]["code"]) == (status, code)
    assert conn.execute("SELECT COUNT(*) FROM reconciliation_log").fetchone()[0] == before


def test_an_unknown_incident_is_a_404(world):
    client, _conn, _report, older, _newer = world
    response = client.post(
        "/reconciliations/99999/override", data=json.dumps({"version_id": older, "reason": "why"}), content_type="application/json"
    )
    assert response.status_code == 404


def test_the_purge_removes_versions_and_their_log_after_24_hours(world):
    _client, conn, report, *_ = world
    result = purge(conn, now=NOW + timedelta(hours=25))
    assert result["purged"]["incident_versions"] == 2 and result["purged"]["reconciliation_log"] == 1
    assert conn.execute("SELECT COUNT(*) FROM incident_versions WHERE report_id = ?", (report,)).fetchone()[0] == 0
