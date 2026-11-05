"""Self-review fixes: 6.4 (reported time is normalised to UTC so queue order is
real time order) and 2.4 (reserve really is safe when callers run at once)."""


import glob
import json
import sqlite3
import threading

import pytest

from src.intake_gateway.queue import set_connected
from src.unit_registry.service import RegistryError, reserve


def load_schema_and_seed(c):
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "ts.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    c = sqlite3.connect(db_path)
    load_schema_and_seed(c)
    c.close()
    set_connected(True)
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = True
    with app.test_client() as tc:
        yield tc, db_path
    set_connected(True)


def report(stamp, location):
    return {
        "location": location,
        "severity_raw": "chest pain",
        "timestamp_reported": stamp,
        "reporting_unit": "field-unit-7",
    }


@pytest.mark.covers("FR-INTAKE-01-AC2")
def test_offline_queue_orders_by_real_time_across_time_zones(client):
    tc, _db = client
    tc.post("/connectivity", json={"connected": False})
    # 07:30 in UTC-5 is 12:30 UTC, which is LATER than 12:10 UTC, even though
    # the text "2026-11-01T07..." sorts before "2026-11-01T12...".
    later = tc.post("/reports", json=report("2026-11-01T07:30:00-05:00", "later")).get_json()
    earlier = tc.post("/reports", json=report("2026-11-01T12:10:00Z", "earlier")).get_json()

    drained = tc.post("/connectivity", json={"connected": True}).get_json()["drained"]

    assert [d["report_id"] for d in drained] == [earlier["report_id"], later["report_id"]]


@pytest.mark.covers("FR-INTAKE-02-AC1")
def test_an_invalid_time_is_rejected_and_nothing_is_stored(client):
    tc, db = client
    resp = tc.post("/reports", json=report("sometime tuesday", "x"))
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "INVALID_TIMESTAMP"
    c = sqlite3.connect(db)
    assert c.execute("SELECT count(*) FROM incident_reports").fetchone()[0] == 0
    c.close()


def test_eight_threads_reserving_one_unit_exactly_one_wins(tmp_path):
    db_path = tmp_path / "race.sqlite"
    setup = sqlite3.connect(db_path)
    setup.row_factory = sqlite3.Row
    load_schema_and_seed(setup)
    proposal_ids = []
    for _ in range(8):
        report_id = setup.execute(
            "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
            "timestamp_reported, reporting_unit, status, received_at, severity) "
            "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
        ).lastrowid
        proposal_ids.append(
            setup.execute(
                "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
                "recommended_unit_id, reasoning, alternatives, model_identifier, "
                "model_version, generated_at) VALUES (?, 1, 90, 1, 'r', ?, 'fake', '1', 't')",
                (report_id, json.dumps([])),
            ).lastrowid
        )
    setup.commit()
    setup.close()

    barrier = threading.Barrier(8)
    outcomes = []
    lock = threading.Lock()

    def attempt(proposal_id):
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            barrier.wait()
            reserve(conn, 1, proposal_id)
            result = "won"
        except RegistryError as exc:
            result = exc.code
        finally:
            conn.close()
        with lock:
            outcomes.append((proposal_id, result))

    threads = [threading.Thread(target=attempt, args=(pid,)) for pid in proposal_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    results = [r for _, r in outcomes]
    assert len(results) == 8
    assert results.count("won") == 1
    assert results.count("UNIT_ALREADY_RESERVED") == 7

    check = sqlite3.connect(db_path)
    holder = check.execute("SELECT reserved_by_proposal_id FROM units WHERE id = 1").fetchone()[0]
    check.close()
    winner = next(pid for pid, r in outcomes if r == "won")
    assert holder == winner  # the unit belongs to the one thread that was told it won

