"""DEF-029: answers from a real model need a stricter bar than 75 before a unit is dispatched with no human."""
import sqlite3

import pytest

from src.decide_proposal.service import decide_auto, needs_human
from tests.unit.test_human_decision import held_proposal, load_schema_and_seed

REAL = "ollama/qwen3:1.7b"


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "def029.sqlite")
    c.row_factory = sqlite3.Row
    load_schema_and_seed(c)
    yield c
    c.close()


@pytest.mark.covers("FR-AGENT-03-AC2")
@pytest.mark.parametrize(("confidence", "held"), [(74, True), (75, True), (84, True), (85, False), (100, False)])
def test_a_real_model_answer_below_the_stricter_bar_is_held_for_a_person(confidence, held):
    assert needs_human(confidence, "Moderate", model_identifier=REAL) is held


@pytest.mark.parametrize(("confidence", "held"), [(74, True), (75, False)])
def test_the_rules_tier_keeps_the_specified_threshold_of_75(confidence, held):
    assert needs_human(confidence, "Moderate", model_identifier="fake-rules") is held
    assert needs_human(confidence, "Moderate") is held  # no model named: the spec's rule


@pytest.mark.parametrize("severity", ["Severe", "Critical"])
def test_high_severity_is_always_held_whatever_the_model_or_confidence(severity):
    assert needs_human(100, severity, model_identifier=REAL) and needs_human(100, severity)


def test_the_stricter_bar_can_be_changed_without_a_redeploy(monkeypatch):
    monkeypatch.setenv("MODEL_AUTO_APPROVE_MIN", "90")
    assert needs_human(89, "Moderate", model_identifier=REAL) and not needs_human(90, "Moderate", model_identifier=REAL)
    monkeypatch.setenv("MODEL_AUTO_APPROVE_MIN", "nonsense")
    assert needs_human(80, "Moderate", model_identifier=REAL)  # a bad value falls back to the default, never to a looser bar


def test_the_bar_can_never_be_set_below_the_specified_75(monkeypatch):
    monkeypatch.setenv("MODEL_AUTO_APPROVE_MIN", "10")
    assert needs_human(74, "Moderate", model_identifier=REAL) and needs_human(80, "Moderate", model_identifier=REAL)


@pytest.mark.covers("FR-AGENT-03-AC2")
def test_decide_auto_holds_a_real_model_proposal_at_75_but_approves_a_rules_proposal_at_75(conn):
    real, _ = held_proposal(conn, confidence=75, severity="Moderate", unit_id=1)
    conn.execute("UPDATE agent_proposals SET model_identifier = ? WHERE id = ?", (REAL, real))
    rules, _ = held_proposal(conn, confidence=75, severity="Moderate", unit_id=2)
    conn.commit()
    assert decide_auto(conn, real).get("held_for_human") is True
    assert decide_auto(conn, rules)["final_status"] == "approved"
