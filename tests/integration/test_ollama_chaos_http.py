"""Chaos reps: the model server fails in each way the design lists, through the real intake route and database.

The stub is a real HTTP server on 127.0.0.1 (tests/ollama_stub.py). Each test provokes one failure and asserts
what the dispatcher-visible record shows: the report is still classified, by the next tier, and says so.
"""
import glob
import json
import sqlite3
from pathlib import Path

import pytest

from src.scenario.reader import play_scenario
from tests.ollama_stub import GOOD, StubOllama

SCENARIO = Path("seed/scenarios/demo-scenario.json")
PRIMARY = "ollama/qwen3:1.7b"
RULES = "fake-rules"


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "chaos.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    conn.close()
    stub = StubOllama().start()
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_URL", stub.url)
    monkeypatch.setenv("OLLAMA_TIMEOUT", "10")
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, db_path, stub, monkeypatch
    stub.stop()


def send(client, text="person fell, visible leg injury, conscious and talking", place="4th & Main St"):
    body = {"location": place, "severity_raw": text, "timestamp_reported": "2026-11-01T12:00:00+00:00", "reporting_unit": "field-unit-7"}
    return client.post("/reports", data=json.dumps(body), content_type="application/json")


def first_proposals(db):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT report_id, model_identifier, confidence, reasoning FROM agent_proposals WHERE id IN (SELECT MIN(id) FROM agent_proposals GROUP BY report_id) ORDER BY report_id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@pytest.mark.covers("FR-DEGRADE-02-AC1")
def test_with_the_model_up_the_proposal_comes_from_it_and_names_it(world):
    client, db, stub, _ = world
    response = send(client)
    assert response.status_code == 201
    only = first_proposals(db)[0]
    assert only["model_identifier"] == PRIMARY and only["confidence"] == GOOD["confidence"] and len(stub.requests) == 1


@pytest.mark.covers("FR-DEGRADE-02-AC1")
def test_with_the_model_server_down_the_report_is_still_classified_by_the_rules_tier_and_says_so(world):
    client, db, stub, _ = world
    stub.stop()
    response = send(client)
    assert response.status_code == 201
    only = first_proposals(db)[0]
    assert only["model_identifier"] == RULES
    assert only["reasoning"].startswith("[Answered by the rules tier because the primary tier failed.]")


@pytest.mark.covers("FR-DEGRADE-02-AC1")
@pytest.mark.parametrize("mode", ["429", "503", "500", "garbage", "prose", "wrong_shape", "no_message", "redirect"])
def test_each_failure_mode_of_the_model_server_falls_back_instead_of_failing_the_report(world, mode):
    client, db, stub, _ = world
    stub.mode = mode
    assert send(client).status_code == 201
    assert first_proposals(db)[0]["model_identifier"] == RULES


def test_a_slow_model_server_is_cut_off_at_the_time_cap_and_the_report_still_goes_through(world):
    client, db, stub, monkeypatch = world
    monkeypatch.setenv("OLLAMA_TIMEOUT", "0.3")
    stub.mode, stub.delay = "slow", 1.5
    assert send(client).status_code == 201
    assert first_proposals(db)[0]["model_identifier"] == RULES


@pytest.mark.covers("FR-DEGRADE-02-AC1")
def test_the_model_dying_in_the_middle_of_a_scenario_degrades_the_rest_of_it_and_nothing_crashes(world):
    client, db, stub, _ = world
    statuses = []

    def submit(payload):
        statuses.append(client.post("/reports", data=json.dumps(payload), content_type="application/json").status_code)
        if len(statuses) == 1:
            stub.stop()  # the model server dies after the first report

    play_scenario(SCENARIO, 1000, submit, sleep=lambda _s: None)

    assert all(code < 500 for code in statuses) and len(statuses) == 3
    assert [p["model_identifier"] for p in first_proposals(db)] == [PRIMARY, RULES, RULES]


def test_the_kill_switch_takes_effect_on_the_next_report_with_no_restart_and_no_call_to_the_server(world):
    client, db, stub, monkeypatch = world
    send(client)
    assert len(stub.requests) == 1
    monkeypatch.setenv("OLLAMA_ENABLED", "0")
    send(client, place="9th & Pine")
    assert len(stub.requests) == 1  # nothing was sent
    assert [p["model_identifier"] for p in first_proposals(db)] == [PRIMARY, RULES]


def test_a_model_that_answers_badly_every_time_never_gets_more_than_two_calls_per_report(world):
    client, _db, stub, _ = world
    stub.mode = "wrong_shape"
    send(client)
    assert len(stub.requests) == 2
