"""DEF-030 (the purge must run by itself) and DEF-031 (browser security headers)."""
import glob
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.purge.job import PurgeFailed, run_once


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "def030.sqlite"
    monkeypatch.setenv("DB_PATH", str(path))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    for m in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(m).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    conn.commit()
    yield conn, path
    conn.close()


def add_report(conn, received_at):
    conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at) "
        "VALUES (1, 'x', 'y', 't', 'u', 'created', ?)",
        (received_at,),
    )
    conn.commit()


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_the_scheduled_run_deletes_what_is_older_than_24_hours_and_keeps_the_rest(db):
    conn, path = db
    add_report(conn, (datetime.now(UTC) - timedelta(hours=25)).isoformat())
    add_report(conn, (datetime.now(UTC) - timedelta(hours=1)).isoformat())

    def factory():
        c = sqlite3.connect(path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        return c

    result = run_once(factory)

    assert result["purged"]["incident_reports"] == 1
    assert conn.execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0] == 1


def test_a_failed_scheduled_purge_is_reported_loudly_and_does_not_kill_the_job(db, monkeypatch):
    _conn, path = db
    messages = []

    def broken(*args, **kwargs):
        raise PurgeFailed("disk is full")

    monkeypatch.setattr("src.purge.job.purge", broken)
    assert run_once(lambda: sqlite3.connect(path), log=messages.append) is None
    assert messages and "purge failed" in messages[0].lower() and "disk is full" in messages[0]


@pytest.mark.covers("NFR-PRIV-01-AC1")
def test_the_app_starts_the_purge_job_when_it_is_switched_on_and_not_otherwise(db, monkeypatch):
    from src.web_ui.app import create_app

    def alive():
        return [t for t in threading.enumerate() if t.name == "purge-job" and t.is_alive()]

    before = len(alive())
    monkeypatch.delenv("PURGE_CHECK_SECONDS", raising=False)
    create_app()
    assert len(alive()) == before  # off unless PURGE_CHECK_SECONDS is set, so tests and imports start nothing
    monkeypatch.setenv("PURGE_CHECK_SECONDS", "3600")
    create_app()
    assert len(alive()) == before + 1


def test_the_start_script_turns_the_purge_job_on_by_default():
    text = Path("script/start").read_text(encoding="utf-8")
    assert "PURGE_CHECK_SECONDS" in text


@pytest.mark.parametrize("path", ["/healthz", "/dispatcher", "/connectivity", "/nope-404"])
def test_every_response_carries_the_browser_security_headers(db, path):
    from src.web_ui.app import create_app

    client = create_app().test_client()
    headers = client.get(path).headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    policy = headers["Content-Security-Policy"]
    for part in ("default-src 'self'", "frame-ancestors 'none'", "form-action 'self'", "base-uri 'none'"):
        assert part in policy
    assert "unsafe-inline" not in policy and "unsafe-eval" not in policy
