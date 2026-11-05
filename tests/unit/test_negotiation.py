"""Task 5: conflict resolution against the registry (FR-COORD-01, FR-COORD-03)."""
import glob
import json
import sqlite3
from datetime import UTC, datetime

import pytest

from src.negotiation.service import contest, resolve_conflict, verify_log_entry
from src.unit_registry.service import RegistryError, reserve, reserve_for_proposal

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "negotiation.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    yield c
    c.close()


def proposal(conn, severity="Moderate", text="chest pain", location="somewhere", minute=0, unit=1, alternatives=(2,), description=None):
    """An undecided proposal (and its report). Not reserved: the test decides who holds what."""
    at = f"2026-11-01T12:{minute:02d}:00+00:00"
    report_id = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, "
        "description, status, received_at, severity) VALUES (1, ?, ?, ?, 'u', ?, 'classified', ?, ?)",
        (location, text, at, description, at, severity),
    ).lastrowid
    snapshot = json.dumps({"location": location, "severity_raw": text, "description": description, "timestamp_reported": at, "reporting_unit": "u"})
    pid = conn.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, "
        "model_identifier, model_version, generated_at, input_data) VALUES (?, 1, 50, ?, 'original reasoning', ?, 'fake', '1', ?, ?)",
        (report_id, unit, json.dumps(list(alternatives)), at, snapshot),
    ).lastrowid
    conn.commit()
    return pid


def holder(conn, unit=1, **kw):
    pid = proposal(conn, unit=unit, **kw)
    reserve(conn, unit, pid, now=NOW)
    return pid


def contest_for(conn, challenger):
    return reserve_for_proposal(conn, challenger, now=NOW, on_conflict=contest)


def row(conn, sql, *args):
    return conn.execute(sql, args).fetchone()


@pytest.mark.covers("FR-COORD-01-AC1")
def test_two_proposals_for_the_same_unit_are_resolved_by_severity_first(conn):
    held = holder(conn, severity="Moderate")
    challenger = proposal(conn, severity="Serious")

    result = contest_for(conn, challenger)

    assert result["unit_id"] == 1 and result["retried"] == []  # the higher-severity incident took unit 1
    log = row(conn, "SELECT * FROM tiebreak_log")
    assert (log["winner_proposal_id"], log["loser_proposal_id"], log["reason"]) == (challenger, held, "severity")
    assert row(conn, "SELECT reserved_by_proposal_id FROM units WHERE id = 1")[0] == challenger


@pytest.mark.covers("FR-COORD-01-AC2")
def test_the_loser_gets_the_next_best_available_unit(conn):
    held = holder(conn, severity="Moderate")
    challenger = proposal(conn, severity="Serious")
    contest_for(conn, challenger)

    old = row(conn, "SELECT final_status, decided_by FROM agent_proposals WHERE id = ?", held)
    assert (old["final_status"], old["decided_by"]) == ("rejected", "tiebreak")  # kept as history, not deleted
    replacement = row(conn, "SELECT * FROM agent_proposals WHERE report_id = (SELECT report_id FROM agent_proposals WHERE id = ?) AND id != ?", held, held)
    assert replacement["recommended_unit_id"] == 2 and replacement["final_status"] is None
    assert "tiebreak" in replacement["reasoning"] and "original reasoning" in replacement["reasoning"]
    assert row(conn, "SELECT reserved_by_proposal_id FROM units WHERE id = 2")[0] == replacement["id"]


@pytest.mark.covers("FR-COORD-01-AC1")
def test_the_resolution_is_logged_as_following_the_protocol_with_both_scores(conn):
    holder(conn, severity="Moderate", text="chest pain")
    challenger = proposal(conn, severity="Moderate", text="chest pain bleeding badly", minute=5)
    contest_for(conn, challenger)

    log = row(conn, "SELECT * FROM tiebreak_log")
    assert log["reason"] == "richness" and log["protocol_followed"] == 1
    assert (log["winner_richness"], log["loser_richness"]) == (4, 2)  # recomputable by a stranger (ADR 0007)
    assert verify_log_entry(conn, log["id"]) is True


def test_resolving_the_same_pair_twice_gives_the_same_winner_and_one_log_row(conn):
    a, b = proposal(conn, severity="Serious"), proposal(conn, severity="Minor")
    first = resolve_conflict(conn, a, b, now=NOW)
    second = resolve_conflict(conn, b, a, now=NOW)  # asked the other way round
    assert (first["winner"], first["loser"], first["reason"]) == (second["winner"], second["loser"], second["reason"])
    assert row(conn, "SELECT count(*) FROM tiebreak_log")[0] == 1


def test_a_challenger_that_loses_carries_on_with_its_alternatives_and_the_holder_is_untouched(conn):
    held = holder(conn, severity="Severe")
    challenger = proposal(conn, severity="Moderate")

    result = contest_for(conn, challenger)

    assert result["unit_id"] == 2 and result["retried"] == [1]
    still = row(conn, "SELECT final_status FROM agent_proposals WHERE id = ?", held)
    assert still[0] is None and row(conn, "SELECT reserved_by_proposal_id FROM units WHERE id = 1")[0] == held
    assert row(conn, "SELECT reason FROM tiebreak_log")[0] == "severity"  # the resolution is logged either way


@pytest.mark.covers("FR-COORD-03-AC2")
def test_a_true_tie_keeps_the_loser_as_history_and_acts_on_only_one(conn):
    challenger = proposal(conn, severity="Moderate", text="chest pain", minute=0)  # created first: lower id
    held = holder(conn, severity="Moderate", text="chest pain", minute=0)  # identical on every dimension

    contest_for(conn, challenger)

    log = row(conn, "SELECT * FROM tiebreak_log")
    assert log["reason"] == "true-tie" and log["winner_proposal_id"] == challenger  # the lower id, always
    assert row(conn, "SELECT reserved_by_proposal_id FROM units WHERE id = 1")[0] == challenger  # acted on
    history = row(conn, "SELECT final_status, decided_by FROM agent_proposals WHERE id = ?", held)
    assert (history["final_status"], history["decided_by"]) == ("rejected", "tiebreak")  # kept, not discarded
    assert row(conn, "SELECT count(*) FROM agent_proposals WHERE id IN (?, ?)", challenger, held)[0] == 2  # both validated and stored


@pytest.mark.covers("FR-COORD-03-AC1")
def test_a_conflict_that_is_not_a_unit_claim_uses_the_same_order(conn):
    poor_early = proposal(conn, severity="Moderate", text="pain", minute=0, unit=1)
    rich_late = proposal(conn, severity="Moderate", text="chest pain bleeding badly", minute=9, unit=2)  # a different unit
    same_severity_richer = resolve_conflict(conn, poor_early, rich_late, now=NOW)
    assert (same_severity_richer["winner"], same_severity_richer["reason"]) == (rich_late, "richness")

    serious = proposal(conn, severity="Serious", text="pain", minute=9, unit=2)
    higher = resolve_conflict(conn, rich_late, serious, now=NOW)
    assert (higher["winner"], higher["reason"]) == (serious, "severity")  # severity still comes first


def test_an_assigned_unit_is_never_taken_by_a_tiebreak(conn):
    held = holder(conn, severity="Minor")
    conn.execute("UPDATE agent_proposals SET final_status = 'approved', decided_by = 'auto', decided_at = ? WHERE id = ?", (NOW.isoformat(), held))
    conn.execute("UPDATE units SET status = 'assigned' WHERE id = 1")
    conn.commit()
    challenger = proposal(conn, severity="Critical", alternatives=())

    with pytest.raises(RegistryError) as exc:
        contest_for(conn, challenger)

    assert exc.value.code == "UNIT_ALREADY_RESERVED"
    assert row(conn, "SELECT status FROM units WHERE id = 1")[0] == "assigned"
    assert row(conn, "SELECT count(*) FROM tiebreak_log")[0] == 0  # nothing to resolve: the unit is not contestable


def test_a_bumped_proposal_with_no_other_unit_goes_to_a_human_not_into_silence(conn):
    first = holder(conn, unit=1, severity="Moderate", alternatives=(2,))
    holder(conn, unit=2, severity="Moderate", alternatives=(1,))  # both units are held
    challenger = proposal(conn, severity="Critical", alternatives=())

    contest_for(conn, challenger)

    escalation = row(conn, "SELECT * FROM human_escalations")
    assert escalation["reason"] == "TIEBREAK_LOST_NO_UNIT" and escalation["resolved_at"] is None
    assert escalation["proposal_id"] == first
    assert row(conn, "SELECT report_id FROM agent_proposals WHERE id = ?", first)[0] == escalation["report_id"]


def test_the_tiebreak_log_cannot_be_edited(conn):
    a, b = proposal(conn, severity="Serious"), proposal(conn, severity="Minor")
    resolve_conflict(conn, a, b, now=NOW)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        conn.execute("UPDATE tiebreak_log SET reason = 'richness'")


def test_unknown_or_identical_proposals_are_refused(conn):
    a = proposal(conn)
    with pytest.raises(ValueError):
        resolve_conflict(conn, a, a, now=NOW)
    with pytest.raises(LookupError):
        resolve_conflict(conn, a, 9999, now=NOW)


def test_a_requeued_proposal_whose_unit_is_taken_in_the_gap_escalates_instead_of_vanishing(tmp_path, monkeypatch):
    """Review finding: if reserve() lost a race after the replacement proposal was written, nothing told a person."""
    import glob
    import sqlite3
    from pathlib import Path

    import src.negotiation.service as svc
    from src.unit_registry.service import RegistryError

    c = sqlite3.connect(tmp_path / "gap.sqlite")
    c.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        c.executescript(Path(path).read_text(encoding="utf-8"))
    c.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    rid = c.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at, severity) "
        "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
    ).lastrowid
    pid = c.execute(
        "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, model_identifier, "
        "model_version, generated_at) VALUES (?, 1, 50, 1, 'r', '[2]', 'fake', '1', 't')",
        (rid,),
    ).lastrowid
    c.commit()

    def lost_race(*args, **kwargs):
        raise RegistryError("UNIT_ALREADY_RESERVED", "taken first")

    monkeypatch.setattr(svc, "reserve", lost_race)
    result = svc.requeue_loser(c, pid, 1, pid)

    assert result["requeued"] is False and result["reason"] == "TIEBREAK_LOST_NO_UNIT"
    assert c.execute("SELECT COUNT(*) FROM human_escalations WHERE reason = 'TIEBREAK_LOST_NO_UNIT'").fetchone()[0] == 1
    c.close()
