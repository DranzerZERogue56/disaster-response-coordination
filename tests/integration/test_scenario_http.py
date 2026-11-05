"""Task 7, end to end: the demo scenario played through the real /reports route into a real database."""
import glob
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from src.scenario.reader import play_scenario

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from play_scenario import main as cli_main

SCENARIO = Path("seed/scenarios/demo-scenario.json")


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "scenario_http.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, db_path


def rows(db, sql):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    return out


def test_the_demo_scenario_plays_through_the_real_route_in_order_with_the_right_spacing(world):
    client, db = world
    statuses, sleeps, now = [], [], [0.0]

    def submit(payload):
        statuses.append(client.post("/reports", data=json.dumps(payload), content_type="application/json").status_code)

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    result = play_scenario(SCENARIO, 10, submit, sleep=sleep, clock=lambda: now[0])

    assert statuses == [201, 201, 201] and result["reports_queued"] == 3
    assert sleeps == pytest.approx([6.0, 6.0], rel=0.10)  # a minute apart in the file, six seconds at ten times speed
    stored = rows(db, "SELECT location FROM incident_reports ORDER BY id")
    assert [r["location"] for r in stored] == ["4th & Main St", "Oak Street shelter", "9th & Pine"]
    # the third report is the severe one: it wins the unit the second was holding, and that is logged
    assert [r["reason"] for r in rows(db, "SELECT reason FROM tiebreak_log")] == ["severity"]
    assert rows(db, "SELECT COUNT(*) AS n FROM scenario_runs WHERE scenario_file LIKE '%demo-scenario.json'")[0]["n"] == 1


def test_the_command_line_reports_a_bad_file_and_a_bad_speed_without_playing_anything(world, tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert cli_main([str(bad), "--speed", "5"]) == 2
    assert cli_main([str(SCENARIO), "--speed", "0"]) == 2
    assert "cannot play" in capsys.readouterr().err


def test_the_command_line_stops_loudly_when_the_app_is_not_running(world, capsys):
    # nothing listens on this port; the first report cannot be delivered
    code = cli_main([str(SCENARIO), "--speed", "1000", "--url", "http://127.0.0.1:9"])
    assert code == 1 and "stopped after 0 report(s)" in capsys.readouterr().err
