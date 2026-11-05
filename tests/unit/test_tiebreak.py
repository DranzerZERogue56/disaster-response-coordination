"""Task 4: the tiebreak as a pure function (FR-COORD-01, FR-COORD-03) and the richness score (ADR 0007)."""
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.negotiation.tiebreak import (
    SEVERITY_RANK,
    STOP_WORDS,
    Contender,
    compare,
    richness,
)

PROFILE = settings(derandomize=True, deadline=None, max_examples=200, suppress_health_check=[HealthCheck.too_slow])


def c(pid, severity="Moderate", rich=5, at="2026-11-01T12:00:00+00:00"):
    return Contender(proposal_id=pid, severity=severity, richness=rich, reported_at=at)


# ---- the three steps, in order ----------------------------------------------------------------------


def test_higher_severity_wins_even_if_it_is_poorer_and_later():
    r = compare(c(1, "Moderate", rich=50, at="2026-11-01T12:00:00+00:00"), c(2, "Serious", rich=1, at="2026-11-01T13:00:00+00:00"))
    assert (r.winner, r.loser, r.reason) == (2, 1, "severity")


def test_equal_severity_the_report_with_more_information_wins():
    r = compare(c(1, rich=3), c(2, rich=9))
    assert (r.winner, r.loser, r.reason) == (2, 1, "richness")


def test_equal_severity_and_information_the_earlier_report_wins():
    r = compare(c(1, at="2026-11-01T12:05:00+00:00"), c(2, at="2026-11-01T12:00:00+00:00"))
    assert (r.winner, r.loser, r.reason) == (2, 1, "reported-first")


def test_reported_first_compares_real_moments_across_time_zones():
    # 07:30 at UTC-5 is 12:30 UTC, later than 12:10 UTC, although the text sorts earlier
    r = compare(c(1, at="2026-11-01T07:30:00-05:00"), c(2, at="2026-11-01T12:10:00+00:00"))
    assert r.winner == 2 and r.reason == "reported-first"


def test_identical_on_every_dimension_is_a_true_tie_with_a_deterministic_winner():
    first, second = compare(c(7), c(3)), compare(c(3), c(7))
    assert first.reason == second.reason == "true-tie"
    assert first.winner == second.winner == 3 and first.loser == 7  # the lower id, so it never flips


def test_a_proposal_cannot_be_compared_with_itself():
    with pytest.raises(ValueError):
        compare(c(1), c(1))


def test_an_unknown_severity_is_refused_not_ranked():
    with pytest.raises(ValueError):
        compare(c(1, "Catastrophic"), c(2))


def test_the_five_severity_levels_are_ranked_in_order():
    assert [SEVERITY_RANK[s] for s in ("Minor", "Moderate", "Serious", "Severe", "Critical")] == [1, 2, 3, 4, 5]


# ---- the richness score, as ADR 0007 defines it ------------------------------------------------------


def rich(severity_raw="", description=None, location="somewhere"):
    return richness({"severity_raw": severity_raw, "description": description, "location": location})


def test_each_distinct_content_word_is_one_point():
    assert rich("chest pain bleeding") == 3


def test_stop_words_and_one_letter_words_score_nothing():
    assert rich("the and of a to in") == 0 and rich("x y z") == 0 and "the" in STOP_WORDS


def test_repeating_a_word_adds_nothing_and_case_is_ignored():
    assert rich("pain pain PAIN Pain") == 1


def test_words_in_severity_raw_and_description_are_pooled_and_counted_once():
    # distinct pooled words: chest, pain, worse, when, breathing = 5, plus 2 for having a description
    assert rich("chest pain", "chest pain worse when breathing") == 7
    assert rich("chest pain", None) == 2


def test_a_separate_description_is_worth_two_points_on_top_of_its_words():
    assert rich("pain", "x") == rich("pain", None) + 2  # "x" is no word, so only the bonus counts
    assert rich("pain", "   ") == rich("pain", None)  # a blank description is not a description


@pytest.mark.parametrize("location", ["4th & Main St", "900 Elm Ave", "Main and 3rd", "Elm / Oak", "Unit 12"])
def test_a_specific_location_is_worth_two_points(location):
    assert rich("pain", location=location) == rich("pain", location="somewhere") + 2


@pytest.mark.parametrize("vague", ["near the old warehouse", "somewhere", "behind the bank", "", "near the old warehouse on 2nd", "the 3rd building"])
def test_a_vague_location_earns_no_bonus(vague):
    assert rich("pain", location=vague) == rich("pain", location="somewhere")


def test_the_demo_reports_score_as_a_stranger_would_expect():
    clear = rich("person fell, visible leg injury, conscious and talking", None, "4th & Main St")
    vague = rich("something happened, not sure how bad, no one is answering", None, "near the old warehouse on 2nd")
    # clear: person fell visible leg injury conscious talking = 7 words, plus 2 for the intersection
    # vague: something happened sure how bad one answering = 7 words, and "on 2nd" is not a specific place
    assert (clear, vague) == (9, 7)


# ---- properties ---------------------------------------------------------------------------------------

words = st.text(alphabet="abcdefghij", min_size=2, max_size=6)
contenders = st.builds(
    Contender,
    proposal_id=st.integers(1, 10_000),
    severity=st.sampled_from(sorted(SEVERITY_RANK)),
    richness=st.integers(0, 40),
    reported_at=st.sampled_from([f"2026-11-01T12:{m:02d}:00+00:00" for m in range(10)]),
)


@PROFILE
@given(a=contenders, b=contenders)
def test_property_both_orders_name_the_same_winner(a, b):
    if a.proposal_id == b.proposal_id:
        return
    assert compare(a, b).winner == compare(b, a).winner


@PROFILE
@given(a=contenders, b=contenders, d=contenders)
def test_property_the_tiebreak_has_no_cycles(a, b, d):
    ids = {a.proposal_id, b.proposal_id, d.proposal_id}
    if len(ids) < 3:
        return
    if compare(a, b).winner == a.proposal_id and compare(b, d).winner == b.proposal_id:
        assert compare(a, d).winner == a.proposal_id


@PROFILE
@given(text=st.lists(words, max_size=12), extra=words)
def test_property_a_new_distinct_word_adds_exactly_one_point(text, extra):
    base = rich(" ".join(text))
    if extra in {w for w in text} or extra in STOP_WORDS:
        return
    assert rich(" ".join([*text, extra])) == base + 1


@PROFILE
@given(text=st.lists(words, max_size=12))
def test_property_repeating_the_whole_text_changes_nothing_and_the_score_is_never_negative(text):
    once = rich(" ".join(text))
    assert rich(" ".join(text + text)) == once >= 0
