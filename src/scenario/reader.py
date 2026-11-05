"""Scenario Reader (docs/architecture.md section 5), Milestone 11 / FR-SIM-01.

Replays a prewritten sequence of incident reports at a controlled pace so the defense demo does not depend
on live data. A scenario file is a JSON list; each entry has the time the report is "reported" in the
scenario and the report itself:

    [{"reported_at": "2026-11-01T12:00:00+00:00", "payload": {...}}, ...]

Reports are submitted after the gap they have in the file divided by the speed (60 s apart at speed 10 is 6 s
apart). Each report is scheduled against the start of the play, not against the previous report, so time
spent submitting never stretches the spacing. The whole file is checked before anything is submitted or
recorded: a bad entry halfway down must not leave a half-played scenario. If a submit fails the play stops
with that error; it does not carry on and pretend.
"""
import itertools
import json
import math
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.db import connect


class ScenarioFileInvalid(Exception):
    """The scenario file cannot be played; nothing was submitted."""


@dataclass(frozen=True)
class ScenarioReport:
    reported_at: datetime
    payload: dict


def _moment(text):
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def load_scenario(path):
    """Read and validate a scenario file. Raises ScenarioFileInvalid for anything unplayable."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ScenarioFileInvalid(f"{path.name} cannot be read: {exc}") from exc
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise ScenarioFileInvalid(f"{path.name} is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ScenarioFileInvalid(f"{path.name} must be a non-empty list of reports")

    reports = []
    for index, entry in enumerate(data, start=1):
        where = f"{path.name}, entry {index}"
        if not isinstance(entry, dict):
            raise ScenarioFileInvalid(f"{where}: must be an object")
        stamp = entry.get("reported_at")
        if not isinstance(stamp, str):
            raise ScenarioFileInvalid(f"{where}: reported_at is missing")
        try:
            moment = _moment(stamp)
        except ValueError as exc:
            raise ScenarioFileInvalid(f"{where}: reported_at {stamp!r} is not a readable time") from exc
        if not isinstance(entry.get("payload"), dict):
            raise ScenarioFileInvalid(f"{where}: payload must be an object")
        if reports and moment < reports[-1].reported_at:
            raise ScenarioFileInvalid(f"{where}: reported_at is earlier than the entry before it")
        reports.append(ScenarioReport(moment, entry["payload"]))
    return reports


def _check_speed(speed):
    ok = isinstance(speed, (int, float)) and not isinstance(speed, bool) and math.isfinite(speed) and speed > 0
    if not ok:
        raise ValueError(f"speed must be a finite number above zero, got {speed!r}")


def play_scenario(path, speed, submit, conn=None, sleep=time.sleep, clock=time.monotonic):
    """Play a scenario. `submit(payload)` is called once per report, in order. Returns
    {run_id, reports_queued, started_at, gaps} where gaps are the planned seconds between one report and the
    next (scenario gap divided by speed). `conn` defaults to the app database."""
    _check_speed(speed)
    reports = load_scenario(path)
    gaps = [(b.reported_at - a.reported_at).total_seconds() / speed for a, b in itertools.pairwise(reports)]

    own_connection = conn is None
    conn = conn or connect()
    try:
        started_at = datetime.now(UTC).isoformat()
        run_id = conn.execute(
            "INSERT INTO scenario_runs (mode, scenario_file, team_size_config, started_at) VALUES ('batch', ?, '{}', ?)",
            (str(path), started_at),
        ).lastrowid
        conn.commit()

        begin = clock()
        queued = 0
        for report in reports:
            due = begin + (report.reported_at - reports[0].reported_at).total_seconds() / speed
            wait = due - clock()
            if wait > 0:
                sleep(wait)
            submit(report.payload)
            queued += 1
    finally:
        if own_connection:
            conn.close()
    return {"run_id": run_id, "reports_queued": queued, "started_at": started_at, "gaps": gaps}
