"""Task 3: NFR-PRIV-01 through the real intake route and the real command-line purge."""
import glob
import json
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest

CALLER_NAME = "Quentin Fairweather"
CALLER_PHONE = "555-0187-2241"
REPORT = {
    "location": "4th & Main St",
    "severity_raw": "person fell, visible leg injury, conscious and talking",
    "timestamp_reported": "2026-11-01T12:00:00+00:00",
    "reporting_unit": "field-unit-7",
}


def build_db(path):
    conn = sqlite3.connect(path)
    for migration in sorted(glob.glob("migrations/*.sql")):
        with open(migration, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "privacy.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    build_db(db_path)
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, db_path


def everything_stored(db_path):
    """Every table, every row, every column, as one string: 'anywhere' means anywhere."""
    conn = sqlite3.connect(db_path)
    dump = "\n".join(conn.iterdump())
    conn.close()
    return dump


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_caller_name_and_phone_are_never_persisted_anywhere(world):
    client, db = world
    body = {**REPORT, "caller_name": CALLER_NAME, "caller_phone": CALLER_PHONE, "caller": {"name": CALLER_NAME}}
    resp = client.post("/reports", data=json.dumps(body), content_type="application/json")
    assert resp.status_code == 201

    stored = everything_stored(db)
    assert CALLER_NAME not in stored and "Fairweather" not in stored
    assert CALLER_PHONE not in stored and "2241" not in stored
    assert "caller_" not in stored  # not even the field names


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_the_command_line_purge_removes_old_data_and_reports_what_it_did(world):
    client, db = world
    client.post("/reports", data=json.dumps(REPORT), content_type="application/json")
    env = {**os.environ, "DB_PATH": str(db)}
    far_future = (datetime.now(UTC) + timedelta(hours=25)).isoformat()

    not_yet = subprocess.run([sys.executable, "tools/purge.py"], env=env, capture_output=True, text=True, check=False)
    assert not_yet.returncode == 0 and json.loads(not_yet.stdout)["purged"]["incident_reports"] == 0

    later = subprocess.run([sys.executable, "tools/purge.py", "--now", far_future], env=env, capture_output=True, text=True, check=False)
    result = json.loads(later.stdout)
    assert later.returncode == 0 and result["purged"]["incident_reports"] == 1
    assert result["purged"]["agent_proposals"] == 1 and result["reset"]["units"] == 1


def test_the_command_line_purge_fails_loudly_and_changes_nothing(tmp_path):
    db = tmp_path / "broken.sqlite"
    build_db(db)
    conn = sqlite3.connect(db)
    conn.execute("DROP TABLE notifications")
    conn.commit()
    conn.close()
    env = {**os.environ, "DB_PATH": str(db)}
    run = subprocess.run([sys.executable, "tools/purge.py"], env=env, capture_output=True, text=True, check=False)
    assert run.returncode == 1 and "PURGE_FAILED" in run.stderr
