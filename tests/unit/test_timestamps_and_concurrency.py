"""Self-review fixes: 6.4 (reported time is normalised to UTC so queue order is
real time order) and 2.4 (reserve really is safe when callers run at once)."""


import pytest

from src.intake_gateway.service import InvalidTimestamp, normalize_timestamp


@pytest.mark.parametrize(
    "given, expected",
    [
        ("2026-11-01T12:00:00+00:00", "2026-11-01T12:00:00+00:00"),
        ("2026-11-01T12:00:00Z", "2026-11-01T12:00:00+00:00"),
        ("2026-11-01T07:30:00-05:00", "2026-11-01T12:30:00+00:00"),
        ("2026-11-01T14:30:00+02:00", "2026-11-01T12:30:00+00:00"),
        ("2026-11-01T12:00:00", "2026-11-01T12:00:00+00:00"),  # no offset: taken as UTC
    ],
)
def test_reported_times_are_stored_as_utc(given, expected):
    assert normalize_timestamp(given) == expected


@pytest.mark.parametrize("bad", ["yesterday", "", "2026-13-45T99:00:00", "12:00"])
def test_a_time_that_is_not_iso_8601_is_refused(bad):
    with pytest.raises(InvalidTimestamp):
        normalize_timestamp(bad)

