"""Task 8, end to end: heartbeat, alert and human confirmation through the real routes and database."""
import glob
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.heartbeat.service import check_nodes, heartbeat

T0 = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)  # in the past, so the app's real clock is later


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "heartbeat_http.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.execute("INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (1, 'Fire', 'alive', ?)", (T0.isoformat(),))
    conn.execute("UPDATE agent_nodes SET last_heartbeat_at = ?", (T0.isoformat(),))
    conn.commit()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, conn
    conn.close()


@pytest.mark.covers("FR-DEGRADE-01-AC2")
def test_a_flagged_node_is_recovered_only_when_a_dispatcher_confirms_through_the_route(world):
    client, conn = world
    heartbeat(conn, 1, now=T0 + timedelta(seconds=30))
    check_nodes(conn, now=T0 + timedelta(seconds=30))  # node 2 has been silent for 30 s

    seen = client.get("/alerts").get_json()["alerts"]
    assert len(seen) == 1 and seen[0]["node_id"] == 2
    assert sorted(n["audience"] for n in seen[0]["notices"]) == ["agent", "human"]

    too_early = client.post("/nodes/2/confirm-recovery")
    assert (too_early.status_code, too_early.get_json()["error"]["code"]) == (409, "NODE_NOT_RESUMED")

    assert client.post("/nodes/2/heartbeat").status_code == 200  # the node answers again (the real clock is later than the fake one)
    after = client.get("/alerts").get_json()["alerts"][0]
    assert after["recovered_at"] and all(n["late_recovery"] == 1 for n in after["notices"])
    assert conn.execute("SELECT status FROM agent_nodes WHERE id = 2").fetchone()[0] == "not_responding"

    done = client.post("/nodes/2/confirm-recovery")
    assert done.status_code == 200 and done.get_json()["status"] == "recovered"
    assert conn.execute("SELECT status FROM agent_nodes WHERE id = 2").fetchone()[0] == "recovered"


def test_unknown_nodes_and_unflagged_nodes_get_clear_errors(world):
    client, _conn = world
    assert client.post("/nodes/999/heartbeat").status_code == 404
    assert client.post("/nodes/999/confirm-recovery").status_code == 404
    unflagged = client.post("/nodes/1/confirm-recovery")
    assert (unflagged.status_code, unflagged.get_json()["error"]["code"]) == (409, "NODE_NOT_FLAGGED")
