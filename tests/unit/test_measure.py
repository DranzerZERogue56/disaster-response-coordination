from src.classify_propose.measure import SEED_REPORTS, measure, percentile, render
from src.classify_propose.model import FakeModel


def test_there_are_twenty_seeded_reports():
    assert len(SEED_REPORTS) == 20


def test_percentile_is_nearest_rank():
    values = list(range(1, 21))  # 1..20
    assert percentile(values, 0.95) == 19
    assert percentile(values, 0.50) == 10
    assert percentile([7], 0.95) == 7


def test_measure_runs_all_twenty_and_reports_the_spread():
    result = measure(FakeModel())

    assert result["reports"] == 20
    assert result["model"] == "fake-rules v1"
    assert 0 < result["p95_seconds"] <= result["max_seconds"]
    assert result["within_limit"] is True
    assert result["confidence_min"] <= result["confidence_mean"] <= result["confidence_max"]
    assert 0 < result["under_75"] < 20  # the set mixes clear and vague reports
    assert 0.0 <= result["human_review_share"] <= 1.0


def test_the_written_report_is_honest_about_the_fake_model():
    text = render(measure(FakeModel()))
    assert "NFR-PERF-01" in text
    assert "not met until the same command is run with the real model" in text

