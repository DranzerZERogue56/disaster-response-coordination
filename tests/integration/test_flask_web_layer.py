"""Flask web-layer hardening (docs/flask-template-audit.md): Host header, cache headers, request size, console size."""
import glob
import json
import sqlite3
from pathlib import Path

import pytest

GOOD = {"location": "4th & Main St", "severity_raw": "person fell", "timestamp_reported": "2026-11-01T12:00:00+00:00", "reporting_unit": "u"}


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "web.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.delenv("AUTH_ENFORCED", raising=False)
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    conn.close()
    from src.web_ui.app import create_app

    app = create_app()
    with app.test_client() as client:
        yield client, db_path


@pytest.mark.defect("DEF-036")
@pytest.mark.parametrize("host", ["evil.example", "evil.example:8080", "127.0.0.1.evil.example", "localhost.evil.example"])
def test_a_request_for_a_foreign_host_name_is_refused(world, host):
    client, _ = world
    assert client.get("/healthz", headers={"Host": host}).status_code == 400


@pytest.mark.defect("DEF-036")
@pytest.mark.parametrize("host", ["localhost", "localhost:8080", "127.0.0.1", "127.0.0.1:8080"])
def test_the_machines_own_names_are_still_served(world, host):
    client, _ = world
    assert client.get("/healthz", headers={"Host": host}).status_code == 200


@pytest.mark.defect("DEF-036")
def test_a_state_changing_request_for_a_foreign_host_changes_nothing(world):
    client, db_path = world
    body = json.dumps(GOOD)
    response = client.post("/reports", data=body, content_type="application/json", headers={"Host": "evil.example"})
    assert response.status_code == 400
    assert sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0] == 0


@pytest.mark.defect("DEF-037")
@pytest.mark.parametrize("path", ["/dispatcher", "/login", "/healthz", "/proposals/pending"])
def test_pages_and_data_are_never_stored_by_the_browser_or_a_proxy(world, path):
    client, _ = world
    assert "no-store" in client.get(path).headers.get("Cache-Control", "")


@pytest.mark.defect("DEF-038")
def test_a_request_body_over_one_megabyte_is_refused_with_413_and_stores_nothing(world):
    client, db_path = world
    body = json.dumps({**GOOD, "description": "A" * (2 * 1024 * 1024)})
    assert client.post("/reports", data=body, content_type="application/json").status_code == 413
    assert sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0] == 0


@pytest.mark.defect("DEF-038")
def test_a_form_with_thousands_of_fields_is_refused(world):
    client, _ = world
    fields = {f"f{i}": "x" for i in range(3000)}
    response = client.post("/login", data=fields, content_type="multipart/form-data")
    assert response.status_code == 413


@pytest.mark.defect("DEF-038")
def test_a_normal_report_is_still_accepted(world):
    client, _ = world
    assert client.post("/reports", data=json.dumps(GOOD), content_type="application/json").status_code == 201


@pytest.mark.defect("DEF-039")
def test_the_console_shows_at_most_200_waiting_proposals_oldest_first_and_says_how_many_are_hidden(world):
    client, db_path = world
    conn = sqlite3.connect(db_path)
    for n in range(250):
        report_id = conn.execute(
            "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at, severity) "
            "VALUES (1, ?, 'x', 't', 'u', 'classified', '2999-01-01T00:00:00+00:00', 'Moderate')",
            (f"loc {n}",),
        ).lastrowid
        conn.execute(
            "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, model_identifier, model_version, generated_at) "
            "VALUES (?, 1, 50, 1, 'r', '[]', 'fake', '1', '2999-01-01T00:00:00+00:00')",
            (report_id,),
        )
    conn.commit()
    conn.close()
    html = client.get("/dispatcher").get_data(as_text=True)
    assert html.count('class="incident"') == 200
    assert "50 more" in html
    assert "loc 0<" in html or "loc 0\n" in html or ": loc 0" in html
    assert ": loc 249<" not in html
