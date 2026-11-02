import glob
import sqlite3
from datetime import UTC, datetime

import pytest

from src.decide_proposal.service import decide_auto, decide_human, stub_dispatcher_id
from src.notify_responder.service import (
    NotifyError,
    notify_for_decision,
    notify_responder,
)
from src.unit_registry.service import reserve

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def load_schema_and_seed(c):
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "test.sqlite")
    c.row_factory = sqlite3.Row
    load_schema_and_seed(c)
    yield c
    c.close()


def reserved_proposal(conn, confidence=90, severity="Moderate", unit_id=1):
    report_id = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', ?)",
        (severity,),
    ).lastrowid
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
        "recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at) VALUES (?, 1, ?, ?, 'r', '[]', 'fake', '1', 't')",
        (report_id, confidence, unit_id),
    ).lastrowid
    conn.commit()
    reserve(conn, unit_id, pid, now=T0)
    return pid


def notifications(conn):
    return conn.execute("SELECT * FROM notifications ORDER BY id").fetchall()


def test_notification_row_has_sent_at_and_no_acknowledgment(conn):
    pid = reserved_proposal(conn)
    decide_auto(conn, pid)
    result = notify_responder(conn, pid, 1, now=T0)

    (row,) = notifications(conn)
    assert (row["assignment_id"], row["unit_id"]) == (pid, 1)
    assert row["sent_at"] == T0.isoformat() == result["sent_at"]
    assert row["acknowledged_at"] is None


def test_nothing_is_sent_for_a_unit_that_is_only_reserved(conn):
    pid = reserved_proposal(conn, confidence=40)  # held, never approved
    with pytest.raises(NotifyError) as exc:
        notify_responder(conn, pid, 1)
    assert exc.value.code == "NOT_ASSIGNED"
    assert notifications(conn) == []


def test_nothing_is_sent_for_another_proposals_unit(conn):
    first = reserved_proposal(conn, unit_id=1)
    second = reserved_proposal(conn, unit_id=2)
    decide_auto(conn, first)
    with pytest.raises(NotifyError):
        notify_responder(conn, second, 1)  # unit 1 belongs to `first`
    assert notifications(conn) == []


def test_notifying_twice_makes_two_rows(conn):
    pid = reserved_proposal(conn)
    decide_auto(conn, pid)
    notify_responder(conn, pid, 1)
    notify_responder(conn, pid, 1)
    assert len(notifications(conn)) == 2


def test_notify_for_decision_skips_held_rejected_and_repeats(conn):
    held = reserved_proposal(conn, confidence=40, unit_id=1)
    assert notify_for_decision(conn, decide_auto(conn, held)) is None

    dispatcher = stub_dispatcher_id(conn)
    rejected = decide_human(conn, held, "reject", dispatcher)
    assert notify_for_decision(conn, rejected) is None

    auto = reserved_proposal(conn, unit_id=1)
    decision = decide_auto(conn, auto)
    assert notify_for_decision(conn, decision)["unit_id"] == 1
    assert notify_for_decision(conn, decide_auto(conn, auto)) is None  # repeat call
    assert len(notifications(conn)) == 1

