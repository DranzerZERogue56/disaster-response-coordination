"""Task 7: the Scenario Reader replays a prewritten sequence of reports at a controlled pace (FR-SIM-01)."""
import glob
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.scenario.reader import ScenarioFileInvalid, load_scenario, play_scenario

START = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


class FakeTime:
    """A clock that only moves when something sleeps, so timing tests take no real time."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "scenario.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    yield c
    c.close()


def write_scenario(tmp_path, offsets_seconds, name="scenario.json"):
    entries = [
        {
            "reported_at": (START + timedelta(seconds=s)).isoformat(),
            "payload": {"synthetic": True, "location": f"{i} Main St", "severity_raw": f"report number {i}"},
        }
        for i, s in enumerate(offsets_seconds)
    ]
    path = tmp_path / name
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def play(path, speed, conn, submitted=None):
    fake = FakeTime()
    submitted = [] if submitted is None else submitted
    result = play_scenario(path, speed, submitted.append, conn=conn, sleep=fake.sleep, clock=fake.clock)
    return result, submitted, fake


@pytest.mark.covers("FR-SIM-01-AC2")
def test_reports_sixty_seconds_apart_arrive_six_seconds_apart_at_ten_times_speed(tmp_path, conn):
    path = write_scenario(tmp_path, [0, 60, 120])
    result, submitted, fake = play(path, 10, conn)
    assert len(submitted) == 3
    assert result["gaps"] == pytest.approx([6.0, 6.0], rel=0.10)
    assert fake.sleeps == pytest.approx([6.0, 6.0], rel=0.10)


@pytest.mark.covers("FR-SIM-01-AC2")
def test_uneven_gaps_keep_their_proportions_and_the_first_report_is_not_delayed(tmp_path, conn):
    path = write_scenario(tmp_path, [0, 30, 150])  # gaps 30 s and 120 s
    result, _, fake = play(path, 2, conn)
    assert result["gaps"] == pytest.approx([15.0, 60.0], rel=0.10)
    assert len(fake.sleeps) == 2  # nothing waits before report one


@pytest.mark.covers("FR-SIM-01-AC2")
def test_the_same_scenario_at_the_same_speed_repeats_order_and_spacing(tmp_path, conn):
    path = write_scenario(tmp_path, [0, 45, 50, 200])
    first, first_sent, first_fake = play(path, 5, conn)
    second, second_sent, second_fake = play(path, 5, conn)
    assert first_sent == second_sent and [p["location"] for p in first_sent] == ["0 Main St", "1 Main St", "2 Main St", "3 Main St"]
    assert first["gaps"] == second["gaps"] and first_fake.sleeps == second_fake.sleeps


def test_time_spent_submitting_is_not_added_to_the_gap(tmp_path, conn):
    """A slow submit must not stretch the spacing: the next report is due at its scheduled moment."""
    path = write_scenario(tmp_path, [0, 60, 120])
    fake = FakeTime()

    def slow_submit(_payload):
        fake.now += 2.0  # the app takes two seconds to answer

    play_scenario(path, 10, slow_submit, conn=conn, sleep=fake.sleep, clock=fake.clock)
    assert fake.sleeps == pytest.approx([4.0, 4.0])  # 6 s apart in total, not 8


def test_equal_times_are_submitted_together(tmp_path, conn):
    path = write_scenario(tmp_path, [0, 0, 10])
    result, submitted, _ = play(path, 1, conn)
    assert len(submitted) == 3 and result["gaps"] == [0.0, 10.0]


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        "",
        '{"reported_at": "2026-11-01T12:00:00+00:00"}',  # an object, not a list
        "[]",  # nothing to play
        '["a string"]',
        '[{"payload": {"location": "x"}}]',  # no time
        '[{"reported_at": "yesterday", "payload": {"location": "x"}}]',  # unreadable time
        '[{"reported_at": "2026-11-01T12:00:00+00:00"}]',  # no payload
        '[{"reported_at": "2026-11-01T12:00:00+00:00", "payload": "text"}]',  # payload not an object
        '[{"reported_at": "2026-11-01T12:01:00+00:00", "payload": {}}, {"reported_at": "2026-11-01T12:00:00+00:00", "payload": {}}]',  # unsorted
    ],
)
def test_a_malformed_scenario_fails_before_any_report_is_submitted(tmp_path, conn, content):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    submitted = []
    with pytest.raises(ScenarioFileInvalid):
        play_scenario(path, 1, submitted.append, conn=conn, sleep=lambda s: None, clock=lambda: 0.0)
    assert submitted == []
    assert conn.execute("SELECT COUNT(*) FROM scenario_runs").fetchone()[0] == 0  # no run recorded either


def test_a_missing_file_is_a_clear_error_not_a_crash(tmp_path):
    with pytest.raises(ScenarioFileInvalid, match="cannot be read"):
        load_scenario(tmp_path / "nope.json")


def test_a_second_bad_entry_deep_in_the_file_still_stops_everything(tmp_path, conn):
    path = tmp_path / "late-bad.json"
    good = {"reported_at": START.isoformat(), "payload": {"location": "x"}}
    path.write_text(json.dumps([good, good, {"reported_at": "garbage", "payload": {}}]), encoding="utf-8")
    submitted = []
    with pytest.raises(ScenarioFileInvalid):
        play_scenario(path, 1, submitted.append, conn=conn, sleep=lambda s: None, clock=lambda: 0.0)
    assert submitted == []


@pytest.mark.parametrize("speed", [0, -1, -0.5, float("nan"), float("inf"), "fast", None, True])
def test_speed_zero_or_negative_or_nonsense_is_refused(tmp_path, conn, speed):
    path = write_scenario(tmp_path, [0, 60])
    submitted = []
    with pytest.raises(ValueError, match="speed"):
        play_scenario(path, speed, submitted.append, conn=conn, sleep=lambda s: None, clock=lambda: 0.0)
    assert submitted == []


def test_each_play_gets_its_own_run_id(tmp_path, conn):
    path = write_scenario(tmp_path, [0, 60])
    first, _, _ = play(path, 10, conn)
    second, _, _ = play(path, 10, conn)
    assert first["run_id"] != second["run_id"]
    rows = conn.execute("SELECT scenario_file, mode, started_at FROM scenario_runs ORDER BY id").fetchall()
    assert len(rows) == 2 and rows[0]["scenario_file"].endswith("scenario.json") and rows[0]["mode"] == "batch"
    assert rows[0]["started_at"] == first["started_at"]


def test_reports_queued_counts_what_was_submitted(tmp_path, conn):
    path = write_scenario(tmp_path, [0, 1, 2, 3, 4])
    result, submitted, _ = play(path, 100, conn)
    assert result["reports_queued"] == len(submitted) == 5


def test_a_failing_submit_stops_the_playback_loudly_and_says_how_far_it_got(tmp_path, conn):
    path = write_scenario(tmp_path, [0, 60, 120])
    calls = []

    def flaky(payload):
        calls.append(payload)
        if len(calls) == 2:
            raise RuntimeError("the app is down")

    with pytest.raises(RuntimeError, match="the app is down"):
        play_scenario(path, 10, flaky, conn=conn, sleep=lambda s: None, clock=lambda: 0.0)
    assert len(calls) == 2  # it did not carry on and pretend
