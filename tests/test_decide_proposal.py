import glob
import sqlite3
from datetime import UTC, datetime

import pytest

from src.decide_proposal.service import decide_auto, needs_human
from src.unit_registry.service import (
    RegistryError,
    assign_unit,
    reserve,
)

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "test.sqlite")
    c.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    yield c
    c.close()


def reserved_proposal(conn, confidence, severity, unit_id=1):
    """A proposal for `unit_id` that already holds the reservation."""
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


def proposal(conn, pid):
    return conn.execute("SELECT * FROM agent_proposals WHERE id = ?", (pid,)).fetchone()


def unit_status(conn, unit_id=1):
    return conn.execute("SELECT status FROM units WHERE id = ?", (unit_id,)).fetchone()[0]


# NFR-SEC-02's own five cases, plus the edges around them.
@pytest.mark.parametrize(
    "confidence, severity, held",
    [
        (74, "Moderate", True),
        (75, "Moderate", False),
        (90, "Moderate", False),
        (95, "Severe", True),
        (95, "Critical", True),
        (100, "Serious", False),
        (0, "Minor", True),
        (100, "Severe", True),
    ],
)
def test_safety_rule(confidence, severity, held):
    assert needs_human(confidence, severity) is held


@pytest.mark.parametrize(
    "confidence, severity, held",
    [
        (74, "Moderate", True),
        (75, "Moderate", False),
        (90, "Moderate", False),
        (95, "Severe", True),
        (95, "Critical", True),
    ],
)
def test_dispatch_follows_the_safety_rule_end_to_end(conn, confidence, severity, held):
    pid = reserved_proposal(conn, confidence, severity)
    result = decide_auto(conn, pid)

    row = proposal(conn, pid)
    if held:
        assert result["held_for_human"] is True
        assert (row["final_status"], row["decided_by"], row["decided_at"]) == (None, None, None)
        assert unit_status(conn) == "reserved"  # nothing dispatched
    else:
        assert result["final_status"] == "approved"
        assert (row["final_status"], row["decided_by"]) == ("approved", "auto")
        assert row["decided_at"] is not None
        assert unit_status(conn) == "assigned"


def test_second_call_returns_the_existing_decision(conn):
    pid = reserved_proposal(conn, 90, "Moderate")
    first = decide_auto(conn, pid)
    second = decide_auto(conn, pid)

    assert second["already_decided"] is True
    assert second["decided_at"] == first["decided_at"]
    assert second["decided_by"] == "auto"


def test_lost_reservation_leaves_proposal_undecided(conn):
    pid = reserved_proposal(conn, 90, "Moderate")
    # The unit vanishes some other way (an expired clock now times the whole
    # proposal out, so this simulates the other causes: out of service, a
    # manual edit, or a rejection racing the approval).
    conn.execute(
        "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, "
        "reserved_at = NULL, released_expected_by = NULL WHERE id = 1"
    )
    conn.commit()

    with pytest.raises(RegistryError) as exc:
        decide_auto(conn, pid)

    assert exc.value.code == "UNIT_NO_LONGER_AVAILABLE"
    assert proposal(conn, pid)["final_status"] is None
    assert unit_status(conn) == "available"


def test_assign_unit_refuses_another_proposals_reservation(conn):
    mine = reserved_proposal(conn, 90, "Moderate", unit_id=1)
    other = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
        "recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at) VALUES (1, 1, 90, 1, 'r', '[]', 'fake', '1', 't')"
    ).lastrowid
    conn.commit()

    with pytest.raises(RegistryError) as exc:
        assign_unit(conn, 1, other)
    assert exc.value.code == "UNIT_NO_LONGER_AVAILABLE"
    assert conn.execute("SELECT reserved_by_proposal_id FROM units WHERE id = 1").fetchone()[0] == mine


def test_unknown_proposal(conn):
    with pytest.raises(LookupError):
        decide_auto(conn, 999)
