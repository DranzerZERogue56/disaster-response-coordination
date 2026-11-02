"""Slice 6: the offline queue (FR-INTAKE-01, NFR-REL-03)."""
import glob
import sqlite3

import pytest

from src.intake_gateway.queue import (
    drain_queue,
    queued_report_ids,
    release_queued,
    set_connected,
)


def load_schema_and_seed(c):
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "queue.sqlite"
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
    set_connected(True)  # never leak the offline switch into another test


def report(text, stamp, location="somewhere"):
    return {
        "location": location,
        "severity_raw": text,
        "timestamp_reported": stamp,
        "reporting_unit": "field-unit-7",
    }


def rows(db_path, sql, params=()):
    c = sqlite3.connect(db_path)
    out = c.execute(sql, params).fetchall()
    c.close()
    return out


def go_offline(tc):
    assert tc.post("/connectivity", json={"connected": False}).get_json()["connected"] is False


def test_offline_report_is_saved_as_queued_and_nothing_else_happens(client):
    tc, db = client
    go_offline(tc)
    resp = tc.post("/reports", json=report("person fell, visible leg injury", "2026-11-01T12:00:00+00:00"))

    assert resp.status_code == 202
    body = resp.get_json()
    assert body["status"] == "queued" and "proposal" not in body
    assert rows(db, "SELECT status, severity FROM incident_reports") == [("queued", None)]
    assert rows(db, "SELECT count(*) FROM agent_proposals") == [(0,)]
    assert rows(db, "SELECT count(*) FROM units WHERE status != 'available'") == [(0,)]
    assert tc.get("/connectivity").get_json() == {"connected": False, "queued_reports": 1}


def test_a_malformed_report_is_still_rejected_offline(client):
    tc, db = client
    go_offline(tc)
    resp = tc.post("/reports", json={"location": "only a location"})
    assert resp.status_code == 400
    assert rows(db, "SELECT count(*) FROM incident_reports") == [(0,)]


def test_reconnecting_processes_queued_reports_oldest_first(client):
    tc, db = client
    go_offline(tc)
    # submitted out of order on purpose
    for stamp in ("2026-11-01T12:30:00+00:00", "2026-11-01T12:10:00+00:00", "2026-11-01T12:20:00+00:00"):
        assert tc.post("/reports", json=report("chest pain", stamp, location=stamp)).status_code == 202

    resp = tc.post("/connectivity", json={"connected": True}).get_json()

    assert resp["drained_count"] == 3
    order = [d["report_id"] for d in resp["drained"]]
    by_stamp = dict(rows(db, "SELECT timestamp_reported, id FROM incident_reports"))
    assert order[:3] == [
        by_stamp["2026-11-01T12:10:00+00:00"],
        by_stamp["2026-11-01T12:20:00+00:00"],
        by_stamp["2026-11-01T12:30:00+00:00"],
    ]
    # the oldest report got the first unit
    oldest_id = by_stamp["2026-11-01T12:10:00+00:00"]
    assert rows(
        db,
        "SELECT recommended_unit_id FROM agent_proposals WHERE report_id = ?",
        (oldest_id,),
    ) == [(1,)]
    assert tc.get("/connectivity").get_json() == {"connected": True, "queued_reports": 0}


def test_ten_reports_during_an_outage_none_are_lost(client):
    """NFR-REL-03: 10 reports submitted offline, 0 lost, all processed after."""
    tc, db = client
    go_offline(tc)
    for i in range(10):
        stamp = f"2026-11-01T13:{i:02d}:00+00:00"
        assert tc.post("/reports", json=report("chest pain", stamp)).status_code == 202
    assert rows(db, "SELECT count(*) FROM incident_reports WHERE status = 'queued'") == [(10,)]

    resp = tc.post("/connectivity", json={"connected": True}).get_json()

    assert resp["drained_count"] == 10
    assert rows(db, "SELECT count(*) FROM incident_reports") == [(10,)]
    assert rows(db, "SELECT count(*) FROM incident_reports WHERE status = 'queued'") == [(0,)]
    assert len({d["report_id"] for d in resp["drained"]}) == 10


def test_running_out_of_units_while_draining_loses_nothing_and_does_not_stop(client):
    tc, db = client
    go_offline(tc)
    for i in range(4):  # the seed has only two Medical units
        tc.post("/reports", json=report("chest pain", f"2026-11-01T14:0{i}:00+00:00"))

    resp = tc.post("/connectivity", json={"connected": True}).get_json()

    assert resp["drained_count"] == 4
    errors = [d.get("error") for d in resp["drained"]]
    assert errors.count("UNIT_ALREADY_RESERVED") == 2  # reports 3 and 4 found no free unit
    assert rows(db, "SELECT count(*) FROM incident_reports WHERE status = 'queued'") == [(0,)]
    assert rows(db, "SELECT count(*) FROM incident_reports") == [(4,)]


def test_draining_twice_never_processes_a_report_twice(client):
    tc, db = client
    go_offline(tc)
    tc.post("/reports", json=report("chest pain", "2026-11-01T15:00:00+00:00"))
    first = tc.post("/connectivity", json={"connected": True}).get_json()
    second = tc.post("/connectivity", json={"connected": True}).get_json()

    assert first["drained_count"] == 1 and second["drained_count"] == 0
    assert rows(db, "SELECT count(*) FROM agent_proposals") == [(1,)]


def test_connectivity_flag_must_be_a_real_boolean(client):
    tc, _ = client
    assert tc.post("/connectivity", json={"connected": "yes"}).status_code == 400
    assert tc.post("/connectivity", json={}).status_code == 400


def test_release_queued_is_safe_to_repeat(client):
    _, db = client
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    c.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, status, received_at) "
        "VALUES (1, 'x', 'y', 't', 'u', 'queued', 't')"
    )
    c.commit()
    rid = queued_report_ids(c)[0]
    assert release_queued(c, rid) is True
    assert release_queued(c, rid) is False
    assert drain_queue(c, lambda conn, report_id: report_id) == []
    c.close()
