import glob
import json
import sqlite3

import pytest

from src.classify_propose.model import FakeModel
from src.classify_propose.service import ClassifyError, classify_and_propose


@pytest.fixture
def conn(tmp_path):
    """A fresh database with one scenario run, one Medical node, two Medical units."""
    c = sqlite3.connect(tmp_path / "test.sqlite")
    c.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    c.execute(
        "INSERT INTO scenario_runs (mode, scenario_file, team_size_config, started_at) "
        "VALUES ('interactive', 'test', '{}', '2026-11-01T00:00:00+00:00')"
    )
    c.execute(
        "INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) "
        "VALUES (1, 'Medical', 'alive', '2026-11-01T00:00:00+00:00')"
    )
    for _ in range(2):
        c.execute(
            "INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) "
            "VALUES (1, 'Medical', 1, 'available')"
        )
    c.commit()
    yield c
    c.close()


def add_report(conn, severity_raw, description=None):
    cur = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, description, status, received_at) "
        "VALUES (1, '4th & Main St', ?, '2026-11-01T00:00:00+00:00', 'field-unit-7', ?, "
        "'created', '2026-11-01T00:00:00+00:00')",
        (severity_raw, description),
    )
    conn.commit()
    return cur.lastrowid


class BadModel:
    identifier = "bad"
    version = "0"

    def __init__(self, output):
        self.output = output

    def classify(self, report):
        return self.output


def test_clear_medical_report_gets_severity_and_proposal(conn):
    rid = add_report(conn, "person fell, visible leg injury, conscious and talking")
    result = classify_and_propose(conn, rid, FakeModel())

    assert result["severity"] == "Serious"
    assert result["confidence"] >= 75
    assert result["recommended_unit_id"] == 1
    assert result["alternatives"] == [2]

    report = conn.execute("SELECT severity, status FROM incident_reports WHERE id = ?", (rid,)).fetchone()
    assert (report["severity"], report["status"]) == ("Serious", "classified")

    row = conn.execute("SELECT * FROM agent_proposals WHERE report_id = ?", (rid,)).fetchone()
    assert row["model_identifier"] == "fake-rules"
    assert json.loads(row["alternatives"]) == [2]
    assert row["final_status"] is None  # deciding is a later slice


def test_vague_report_still_proposes_with_low_confidence(conn):
    rid = add_report(conn, "something happened, not sure how bad, no one's answering")
    result = classify_and_propose(conn, rid, FakeModel())

    assert result["confidence"] < 75
    assert conn.execute("SELECT count(*) FROM agent_proposals").fetchone()[0] == 1


def test_out_of_service_units_are_not_proposed(conn):
    conn.execute("UPDATE units SET status = 'out_of_service' WHERE id = 1")
    conn.commit()
    rid = add_report(conn, "chest pain, not breathing well")
    result = classify_and_propose(conn, rid, FakeModel())

    assert result["recommended_unit_id"] == 2
    assert result["alternatives"] == []


def test_invalid_model_output_leaves_report_for_a_human(conn):
    rid = add_report(conn, "chest pain")
    bad = BadModel({"severity": "Catastrophic", "unit_type": "Medical", "confidence": 90, "reasoning": "x"})
    with pytest.raises(ClassifyError) as exc:
        classify_and_propose(conn, rid, bad)

    assert exc.value.code == "MODEL_OUTPUT_INVALID"
    assert conn.execute("SELECT status FROM incident_reports WHERE id = ?", (rid,)).fetchone()[0] == "created"
    assert conn.execute("SELECT count(*) FROM agent_proposals").fetchone()[0] == 0


def test_no_unit_of_needed_type_is_reported_not_guessed(conn):
    rid = add_report(conn, "building on fire, smoke everywhere")
    with pytest.raises(ClassifyError) as exc:
        classify_and_propose(conn, rid, FakeModel())

    assert exc.value.code == "NO_UNIT_OF_TYPE"
    assert conn.execute("SELECT count(*) FROM agent_proposals").fetchone()[0] == 0


def test_classifying_twice_does_not_make_a_second_proposal(conn):
    rid = add_report(conn, "chest pain")
    classify_and_propose(conn, rid, FakeModel())
    with pytest.raises(ClassifyError) as exc:
        classify_and_propose(conn, rid, FakeModel())

    assert exc.value.code == "ALREADY_CLASSIFIED"
    assert conn.execute("SELECT count(*) FROM agent_proposals").fetchone()[0] == 1


def test_unknown_report_id(conn):
    with pytest.raises(ClassifyError) as exc:
        classify_and_propose(conn, 999, FakeModel())
    assert exc.value.code == "REPORT_NOT_FOUND"

