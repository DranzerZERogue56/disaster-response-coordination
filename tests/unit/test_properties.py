"""Property-based tests (Milestone 11, Medium tier). The four properties are stated in prose in
docs/test-plan.md section 3 before they are code here. Hypothesis runs with a fixed seed
(derandomize) and no wall-clock deadline, so a failure is the same failure on every run."""
import glob
import sqlite3
from datetime import UTC, datetime, timedelta, timezone

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from src.classify_propose.model import SEVERITIES, UNIT_TYPES
from src.classify_propose.service import ClassifyError, _validate
from src.decide_proposal.service import (
    DecideError,
    decide_human,
    needs_human,
    stub_dispatcher_id,
)
from src.intake_gateway.service import normalize_timestamp
from src.unit_registry.service import (
    RegistryError,
    release_expired,
    reserve_for_proposal,
)

PROFILE = settings(derandomize=True, deadline=None, max_examples=200, suppress_health_check=[HealthCheck.too_slow])


# ---- P1: the safety rule ----------------------------------------------------------------------


@pytest.mark.covers("FR-AGENT-03-AC1", "FR-AGENT-03-AC2", "NFR-SEC-02-AC1")
@PROFILE
@given(confidence=st.integers(0, 100), severity=st.sampled_from(SEVERITIES))
def test_P1_nothing_bypasses_a_person_unless_confident_and_not_severe(confidence, severity):
    dispatched_alone = not needs_human(confidence, severity)
    assert dispatched_alone == (confidence >= 75 and severity not in ("Severe", "Critical"))


# ---- P2: times keep their order -----------------------------------------------------------------

offsets = st.integers(-23 * 60 - 59, 23 * 60 + 59).map(lambda m: timezone(timedelta(minutes=m)))
moments = st.datetimes(min_value=datetime(1971, 1, 1), max_value=datetime(2100, 1, 1), timezones=offsets)


@pytest.mark.covers("FR-INTAKE-01-AC2")
@PROFILE
@given(a=moments, b=moments)
def test_P2_the_earlier_moment_always_sorts_first_and_everything_is_utc(a, b):
    text_a, text_b = normalize_timestamp(a.isoformat()), normalize_timestamp(b.isoformat())
    for stored, original in ((text_a, a), (text_b, b)):
        parsed = datetime.fromisoformat(stored)
        assert parsed.utcoffset() == timedelta(0)  # stored as UTC
        assert parsed == original  # the same instant, not a different one
    if a < b:
        assert text_a < text_b
    elif a > b:
        assert text_a > text_b
    else:
        assert text_a == text_b


# ---- P3: units are never double-booked ----------------------------------------------------------


class UnitBookkeeping(RuleBasedStateMachine):
    """A random walk through reserve, approve, reject and clock expiry; invariants checked each step."""

    def __init__(self):
        super().__init__()
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        for path in sorted(glob.glob("migrations/*.sql")):
            with open(path, encoding="utf-8") as f:
                self.conn.executescript(f.read())
        with open("seed/iteration-1.sql", encoding="utf-8") as f:
            self.conn.executescript(f.read())
        for _ in range(2):
            self.conn.execute(
                "INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) VALUES (1, 'Medical', 1, 'available')"
            )
        self.conn.commit()
        self.dispatcher = stub_dispatcher_id(self.conn)
        self.now = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
        self.proposals = []

    @rule(candidates=st.lists(st.integers(1, 4), min_size=1, max_size=3, unique=True))
    def propose_and_reserve(self, candidates):
        report_id = self.conn.execute(
            "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, "
            "reporting_unit, status, received_at, severity) VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
        ).lastrowid
        pid = self.conn.execute(
            "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, "
            "alternatives, model_identifier, model_version, generated_at) VALUES (?, 1, 50, ?, 'r', ?, 'fake', '1', ?)",
            (report_id, candidates[0], str(list(candidates[1:])), self.now.isoformat()),
        ).lastrowid
        self.conn.commit()
        self.proposals.append(pid)
        try:
            reserve_for_proposal(self.conn, pid, now=self.now)
        except RegistryError:
            pass  # every candidate was taken: allowed, and nothing may be left half-done

    @rule(data=st.data())
    def approve(self, data):
        if self.proposals:
            pid = data.draw(st.sampled_from(self.proposals))
            try:
                decide_human(self.conn, pid, "approve", self.dispatcher, now=self.now)
            except (RegistryError, DecideError):
                pass

    @rule(data=st.data())
    def reject(self, data):
        if self.proposals:
            pid = data.draw(st.sampled_from(self.proposals))
            try:
                decide_human(self.conn, pid, "reject", self.dispatcher, now=self.now)
            except (RegistryError, DecideError):
                pass

    @rule(seconds=st.integers(0, 600))
    def time_passes(self, seconds):
        self.now += timedelta(seconds=seconds)
        release_expired(self.conn, now=self.now)

    @invariant()
    def no_unit_is_assigned_without_an_approved_proposal(self):
        bad = self.conn.execute(
            "SELECT u.id FROM units u LEFT JOIN agent_proposals p ON p.id = u.reserved_by_proposal_id "
            "WHERE u.status = 'assigned' AND COALESCE(p.final_status, '') NOT IN ('approved', 'modified')"
        ).fetchall()
        assert bad == []

    @invariant()
    def no_proposal_holds_two_units(self):
        rows = self.conn.execute(
            "SELECT reserved_by_proposal_id, count(*) FROM units WHERE status IN ('reserved', 'assigned') "
            "GROUP BY reserved_by_proposal_id HAVING count(*) > 1"
        ).fetchall()
        assert rows == []

    @invariant()
    def every_held_unit_belongs_to_exactly_one_proposal(self):
        rows = self.conn.execute(
            "SELECT id FROM units WHERE status IN ('reserved', 'assigned') AND reserved_by_proposal_id IS NULL"
        ).fetchall()
        assert rows == []

    def teardown(self):
        self.conn.close()


UnitBookkeeping.TestCase.settings = settings(
    derandomize=True, deadline=None, max_examples=60, stateful_step_count=25, suppress_health_check=[HealthCheck.too_slow]
)
TestUnitBookkeeping = pytest.mark.covers("FR-RES-03-AC3")(UnitBookkeeping.TestCase)


# ---- P4: the model's answer is trusted only if it is exactly the right shape ------------------------

junk = st.one_of(st.none(), st.booleans(), st.integers(-5, 150), st.floats(allow_nan=False), st.text(max_size=8), st.lists(st.integers(), max_size=2))
answers = st.fixed_dictionaries(
    {
        "severity": st.one_of(st.sampled_from(SEVERITIES), junk),
        "unit_type": st.one_of(st.sampled_from(UNIT_TYPES), junk),
        "confidence": st.one_of(st.integers(0, 100), junk),
        "reasoning": st.one_of(st.text(max_size=12), junk),
    }
)


def is_exactly_right(answer):
    return (
        isinstance(answer["severity"], str)
        and answer["severity"] in SEVERITIES
        and isinstance(answer["unit_type"], str)
        and answer["unit_type"] in UNIT_TYPES
        and type(answer["confidence"]) is int
        and 0 <= answer["confidence"] <= 100
        and isinstance(answer["reasoning"], str)
        and answer["reasoning"].strip() != ""
    )


@pytest.mark.covers("FR-AGENT-01-AC2")
@pytest.mark.defect("DEF-015")
@pytest.mark.xfail(strict=True, reason="open defect DEF-015: the validator accepts non-text reasoning and boolean confidence")
@PROFILE
@given(answer=answers)
def test_P4_a_model_answer_passes_validation_only_if_it_is_exactly_the_right_shape(answer):
    try:
        _validate(answer)
        accepted = True
    except ClassifyError:
        accepted = False
    assert accepted == is_exactly_right(answer)
