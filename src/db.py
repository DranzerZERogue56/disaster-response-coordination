"""SQLite connection helper — the one place `DB_PATH` is read from the
environment (docs/architecture.md §3, "SQLite database" container).
"""
import os
import sqlite3
from datetime import UTC, datetime


def get_db_path() -> str:
    return os.environ.get("DB_PATH", "data/dev.sqlite")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_scenario_run(conn: sqlite3.Connection) -> int:
    """Walking-skeleton convenience: incident_reports.scenario_run_id is
    NOT NULL (architecture.md §6), and nothing in this slice runs the real
    Roster Competition yet, so make sure one scenario_run row exists to
    hang reports off of rather than requiring one to be created by hand.
    """
    row = conn.execute("SELECT id FROM scenario_runs ORDER BY id LIMIT 1").fetchone()
    if row:
        return row["id"]
    now = datetime.now(UTC).isoformat()
    cur = conn.execute(
        "INSERT INTO scenario_runs (mode, scenario_file, team_size_config, started_at) "
        "VALUES (?, ?, ?, ?)",
        ("interactive", "skeleton-seed", "{}", now),
    )
    conn.commit()
    return cur.lastrowid
