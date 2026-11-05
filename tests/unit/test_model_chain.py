"""Task 10: when the model fails, fall back smaller model -> rules -> a human, never silence (FR-DEGRADE-02)."""
import glob
import sqlite3

import pytest

from src.classify_propose.chain import ChainExhausted, ModelChain, RetryPolicy
from src.classify_propose.service import ClassifyError, classify_and_propose

GOOD = {"severity": "Serious", "unit_type": "Medical", "confidence": 90, "reasoning": "clear injury"}


class Model:
    """A model that answers, or fails the way it is told to. `plan` is consumed one call at a time:
    an exception instance is raised, a dict is returned; once the plan runs out it answers GOOD."""

    def __init__(self, name, plan=()):
        self.identifier = name
        self.version = "1"
        self.plan = list(plan)
        self.calls = 0

    def classify(self, report):
        self.calls += 1
        step = self.plan.pop(0) if self.plan else GOOD
        if isinstance(step, BaseException):
            raise step
        return dict(step)


def dies(name):
    """A model that fails every time it is called."""
    return Model(name, plan=[RuntimeError(f"{name} crashed")] * 1000)


class Sleeper:
    def __init__(self):
        self.sleeps = []

    def __call__(self, seconds):
        self.sleeps.append(seconds)


@pytest.mark.covers("FR-DEGRADE-02-AC1")
def test_a_failing_primary_falls_back_to_the_smaller_model_then_rules():
    primary, smaller, rules = dies("primary"), Model("smaller"), Model("rules")
    chain = ModelChain(primary, smaller, rules, sleep=Sleeper())

    first = chain.classify({"severity_raw": "x"})
    assert first["model_identifier"] == "smaller" and (primary.calls, smaller.calls, rules.calls) == (1, 1, 0)

    smaller2 = dies("smaller")
    primary2, rules2 = dies("primary"), Model("rules")
    second = ModelChain(primary2, smaller2, rules2, sleep=Sleeper()).classify({"severity_raw": "x"})
    assert second["model_identifier"] == "rules"
    assert (primary2.calls, smaller2.calls, rules2.calls) == (1, 1, 1)  # tried in that order, each once


@pytest.mark.covers("FR-DEGRADE-02-AC1")
def test_a_primary_that_crashes_mid_session_is_replaced_from_then_on_not_before():
    primary = Model("primary", plan=[GOOD, RuntimeError("out of memory")])
    chain = ModelChain(primary, Model("smaller"), Model("rules"), sleep=Sleeper())
    assert chain.classify({})["model_identifier"] == "primary"
    assert chain.classify({})["model_identifier"] == "smaller"  # the crash on call two
    assert chain.classify({})["model_identifier"] == "primary"  # and it is used again once it works


@pytest.mark.covers("FR-DEGRADE-02-AC1")
def test_an_answer_that_fails_validation_counts_as_a_failure_and_falls_back():
    garbage = {"severity": "Catastrophic", "unit_type": "Medical", "confidence": 90, "reasoning": "x"}
    chain = ModelChain(Model("primary", plan=[garbage]), Model("smaller"), Model("rules"), sleep=Sleeper())
    assert chain.classify({})["model_identifier"] == "smaller"


def test_the_answer_says_which_tier_gave_it_and_which_failed_first():
    chain = ModelChain(dies("primary"), Model("smaller"), Model("rules"), sleep=Sleeper())
    answer = chain.classify({})
    assert answer["tier"] == "smaller" and "primary" in answer["reasoning"] and answer["reasoning"].endswith("clear injury")
    unchanged = ModelChain(Model("primary"), Model("smaller"), Model("rules"), sleep=Sleeper()).classify({})
    assert unchanged["tier"] == "primary" and unchanged["reasoning"] == "clear injury"  # a healthy primary adds no note


@pytest.mark.covers("FR-DEGRADE-02-AC2")
def test_a_chain_that_fails_everywhere_retries_six_times_ten_seconds_apart_then_escalates():
    models = (dies("primary"), dies("smaller"), dies("rules"))
    sleeper = Sleeper()
    chain = ModelChain(*models, sleep=sleeper)

    with pytest.raises(ChainExhausted) as exc:
        chain.classify({})

    assert sleeper.sleeps == [10.0] * 6  # once every 10 seconds, for a minute
    assert [m.calls for m in models] == [7, 7, 7]  # the first pass plus six retries
    assert exc.value.attempts == 7 and set(exc.value.errors) == {"primary", "smaller", "rules"}


@pytest.mark.covers("FR-DEGRADE-02-AC2")
def test_a_recovering_backup_stops_the_retries():
    rules = Model("rules", plan=[RuntimeError("busy")] * 3)  # fails the first pass and two retries, then works
    sleeper = Sleeper()
    chain = ModelChain(dies("primary"), dies("smaller"), rules, sleep=sleeper)

    answer = chain.classify({})

    assert answer["model_identifier"] == "rules" and sleeper.sleeps == [10.0] * 3 and rules.calls == 4


def test_a_primary_that_comes_back_during_the_retries_is_used():
    primary = Model("primary", plan=[RuntimeError("loading")] * 2)
    chain = ModelChain(primary, dies("smaller"), dies("rules"), sleep=Sleeper())
    assert chain.classify({})["model_identifier"] == "primary"


def test_the_retry_policy_is_configurable_and_defaults_to_the_requirement():
    assert (RetryPolicy().attempts, RetryPolicy().every_seconds) == (6, 10.0)
    sleeper = Sleeper()
    with pytest.raises(ChainExhausted):
        ModelChain(dies("rules"), retry=RetryPolicy(attempts=2, every_seconds=0.5), sleep=sleeper).classify({})
    assert sleeper.sleeps == [0.5, 0.5]


def test_empty_slots_are_skipped_not_treated_as_failures():
    rules = Model("rules")
    chain = ModelChain(None, None, rules, sleep=Sleeper())  # today: only the rules tier exists
    assert chain.classify({})["model_identifier"] == "rules"
    with pytest.raises(ValueError):
        ModelChain(None, None, None)


def test_a_keyboard_interrupt_is_not_swallowed_as_a_model_failure():
    chain = ModelChain(Model("primary", plan=[KeyboardInterrupt()]), Model("smaller"), sleep=Sleeper())
    with pytest.raises(KeyboardInterrupt):
        chain.classify({})


# ---- the caller: an exhausted chain reaches a human, never silence -------------------------------


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "chain.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    yield c
    c.close()


def make_report(conn):
    rid = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at) "
        "VALUES (1, '4th & Main', 'person fell, leg injury', '2026-11-01T12:00:00+00:00', 'u', 'created', '2026-11-01T12:00:00+00:00')"
    ).lastrowid
    conn.commit()
    return rid


@pytest.mark.covers("FR-DEGRADE-02-AC2")
def test_the_escalation_reaches_a_human_never_silence(conn):
    report = make_report(conn)
    chain = ModelChain(dies("primary"), dies("smaller"), dies("rules"), sleep=Sleeper())

    with pytest.raises(ClassifyError) as exc:
        classify_and_propose(conn, report, chain)

    assert exc.value.code == "MODEL_CHAIN_EXHAUSTED" and "rules" in str(exc.value)
    escalations = [dict(r) for r in conn.execute("SELECT report_id, proposal_id, reason, resolved_at FROM human_escalations")]
    assert escalations == [{"report_id": report, "proposal_id": None, "reason": "MODEL_CHAIN_EXHAUSTED", "resolved_at": None}]
    assert conn.execute("SELECT status FROM incident_reports WHERE id = ?", (report,)).fetchone()[0] == "created"  # waits for a person
    assert conn.execute("SELECT COUNT(*) FROM agent_proposals").fetchone()[0] == 0


def test_trying_the_same_report_again_does_not_pile_up_duplicate_escalations(conn):
    report = make_report(conn)
    for _ in range(3):
        with pytest.raises(ClassifyError):
            classify_and_propose(conn, report, ModelChain(dies("rules"), sleep=Sleeper()))
    assert conn.execute("SELECT COUNT(*) FROM human_escalations").fetchone()[0] == 1


def test_the_proposal_records_the_model_that_actually_answered(conn):
    report = make_report(conn)
    result = classify_and_propose(conn, report, ModelChain(dies("primary"), Model("smaller"), Model("rules"), sleep=Sleeper()))
    stored = conn.execute("SELECT model_identifier, model_version, reasoning FROM agent_proposals WHERE id = ?", (result["proposal_id"],)).fetchone()
    assert (stored["model_identifier"], stored["model_version"]) == ("smaller", "1") and "primary" in stored["reasoning"]
