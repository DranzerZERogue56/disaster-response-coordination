"""Regression tests for DEF-014 (the proposal log did not record the data the agent used)."""
import glob
import json
import sqlite3

import pytest

from src.classify_propose.model import FakeModel
from src.classify_propose.service import classify_and_propose


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "input.sqlite")
    c.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    yield c
    c.close()


def make_report(conn, text="person fell, visible leg injury, conscious and talking"):
    cur = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, "
        "reporting_unit, description, status, received_at) "
        "VALUES (1, '4th & Main St', ?, '2026-11-01T12:00:00+00:00', 'field-unit-7', 'near the bank', "
        "'created', '2026-11-01T12:00:00+00:00')",
        (text,),
    )
    conn.commit()
    return cur.lastrowid


@pytest.mark.covers("FR-AUDIT-01-AC1")
@pytest.mark.defect("DEF-014")
def test_the_proposal_records_the_input_data_and_the_confidence_when_it_is_generated(conn):
    result = classify_and_propose(conn, make_report(conn), FakeModel())

    row = conn.execute("SELECT confidence, input_data FROM agent_proposals WHERE id = ?", (result["proposal_id"],)).fetchone()
    assert row["confidence"] == result["confidence"] == 95
    assert json.loads(row["input_data"]) == {
        "description": "near the bank",
        "location": "4th & Main St",
        "reporting_unit": "field-unit-7",
        "severity_raw": "person fell, visible leg injury, conscious and talking",
        "timestamp_reported": "2026-11-01T12:00:00+00:00",
    }


@pytest.mark.defect("DEF-014")
def test_the_recorded_input_survives_the_report_being_changed_or_removed(conn):
    result = classify_and_propose(conn, make_report(conn), FakeModel())
    report_id = conn.execute("SELECT report_id FROM agent_proposals").fetchone()[0]
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("UPDATE incident_reports SET location = 'changed afterwards' WHERE id = ?", (report_id,))
    conn.commit()
    logged = json.loads(conn.execute("SELECT input_data FROM agent_proposals WHERE id = ?", (result["proposal_id"],)).fetchone()[0])
    assert logged["location"] == "4th & Main St"  # what the agent actually saw


@pytest.mark.defect("DEF-014")
def test_the_logged_input_cannot_be_edited_afterwards(conn):
    result = classify_and_propose(conn, make_report(conn), FakeModel())
    with pytest.raises(sqlite3.IntegrityError, match="cannot be changed"):
        conn.execute("UPDATE agent_proposals SET input_data = '{}' WHERE id = ?", (result["proposal_id"],))
    # rewriting the same value is not a change
    same = conn.execute("SELECT input_data FROM agent_proposals WHERE id = ?", (result["proposal_id"],)).fetchone()[0]
    conn.execute("UPDATE agent_proposals SET input_data = ? WHERE id = ?", (same, result["proposal_id"]))
