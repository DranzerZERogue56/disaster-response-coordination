"""Acceptance tests (Milestone 11): one test per acceptance criterion of a built Must requirement.

Each test is named after the criterion it verifies (test_FR_INTAKE_02_AC1_...), is written from the
criterion's Given/when/then text in docs/requirements.md, and drives the system the way a user would:
HTTP requests against the running Flask app on a freshly seeded SQLite database. They check observable
behaviour (responses, and the database rows a reviewer could look at), not internals.

Criteria for requirements that are not built yet (FR-COORD, FR-DEGRADE, FR-SIM replay, ...) have no test:
they show as gaps in docs/traceability.csv. Where a built requirement does not do what its criterion
says, the test is marked as an open defect (xfail strict) with its defect id.
"""
import glob
import json
import re
import sqlite3
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIELDS = ["location", "severity_raw", "timestamp_reported", "reporting_unit"]
CLEAR = "person fell, visible leg injury, conscious and talking"  # fake model: Serious, confidence 95
VAGUE = "something happened, not sure how bad, no one is answering"  # fake model: confidence 40
SEVERE = "man collapsed, chest pain, not breathing well"  # fake model: Severe, confidence 95


def report(text=CLEAR, minute=0, **changes):
    body = {
        "location": "4th & Main St",
        "severity_raw": text,
        "timestamp_reported": f"2026-11-01T12:{minute:02d}:00+00:00",
        "reporting_unit": "field-unit-7",
    }
    body.update(changes)
    return body


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A fresh seeded database (two Medical units, a stand-in dispatcher) behind the real app."""
    db_path = tmp_path / "acceptance.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob(str(REPO / "migrations" / "*.sql"))):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript((REPO / "seed" / "iteration-1.sql").read_text(encoding="utf-8"))
    conn.close()
    from src.intake_gateway.queue import set_connected
    from src.web_ui.app import create_app

    set_connected(True)
    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, db_path
    set_connected(True)


def post(client, body, path="/reports"):
    return client.post(path, data=json.dumps(body), content_type="application/json")


def query(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return out


# ---- FR-INTAKE-01 -------------------------------------------------------------------------


@pytest.mark.covers("FR-INTAKE-01-AC1")
def test_FR_INTAKE_01_AC1_a_complete_report_is_created_and_confirmed(world):
    client, db = world
    resp = post(client, report())
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "created"
    assert query(db, "SELECT id FROM incident_reports WHERE id = ?", (body["report_id"],))


@pytest.mark.covers("FR-INTAKE-01-AC2")
def test_FR_INTAKE_01_AC2_offline_reports_queue_then_process_in_timestamp_order(world):
    client, db = world
    client.post("/connectivity", json={"connected": False})
    ids = {}
    for minute in (30, 10, 20):  # submitted out of order
        resp = post(client, report(minute=minute))
        assert resp.status_code == 202 and resp.get_json()["status"] == "queued"
        ids[minute] = resp.get_json()["report_id"]
    assert len(query(db, "SELECT id FROM incident_reports WHERE status = 'queued'")) == 3

    back = client.post("/connectivity", json={"connected": True}).get_json()

    assert [d["report_id"] for d in back["drained"]] == [ids[10], ids[20], ids[30]]
    assert query(db, "SELECT id FROM incident_reports WHERE status = 'queued'") == []


# ---- FR-INTAKE-02 -------------------------------------------------------------------------


@pytest.mark.covers("FR-INTAKE-02-AC1")
def test_FR_INTAKE_02_AC1_one_missing_field_is_rejected_and_named(world):
    client, db = world
    body = report()
    del body["reporting_unit"]
    resp = post(client, body)
    assert resp.status_code == 400
    error = resp.get_json()["error"]
    assert error["code"] == "FIELD_MISSING" and error["field"] == ["reporting_unit"]
    assert query(db, "SELECT id FROM incident_reports") == []


@pytest.mark.covers("FR-INTAKE-02-AC1")
def test_FR_INTAKE_02_AC1_an_improperly_filled_field_is_rejected_and_named(world):
    client, _ = world
    resp = post(client, report(timestamp_reported="next tuesday-ish"))
    assert resp.status_code == 400
    assert "timestamp_reported" in resp.get_json()["error"]["message"]


@pytest.mark.covers("FR-INTAKE-02-AC2")
def test_FR_INTAKE_02_AC2_every_bad_field_is_listed_top_down_in_one_response(world):
    client, _ = world
    resp = post(client, {"severity_raw": CLEAR})  # three fields missing at once
    assert resp.status_code == 400
    assert resp.get_json()["error"]["field"] == ["location", "timestamp_reported", "reporting_unit"]


# ---- FR-AGENT-01 .. 03 --------------------------------------------------------------------


@pytest.mark.covers("FR-AGENT-01-AC1")
def test_FR_AGENT_01_AC1_a_report_is_tagged_with_a_severity_within_five_seconds(world):
    client, db = world
    start = time.perf_counter()
    resp = post(client, report())
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0
    assert resp.get_json()["proposal"]["severity"] in ("Minor", "Moderate", "Serious", "Severe", "Critical")
    assert query(db, "SELECT severity FROM incident_reports")[0]["severity"] == "Serious"


@pytest.mark.covers("FR-AGENT-01-AC2")
def test_FR_AGENT_01_AC2_an_unsure_classification_goes_to_a_human_and_dispatches_nothing(world):
    client, db = world
    body = post(client, report(VAGUE)).get_json()
    assert body["decision"]["held_for_human"] is True
    pending = client.get("/proposals/pending").get_json()["pending"]
    assert [p["proposal_id"] for p in pending] == [body["proposal"]["proposal_id"]]
    assert query(db, "SELECT id FROM units WHERE status = 'assigned'") == []


@pytest.mark.covers("FR-AGENT-02-AC1")
def test_FR_AGENT_02_AC1_a_proposal_has_a_resource_a_confidence_a_reason_and_alternatives(world):
    client, _ = world
    proposal = post(client, report()).get_json()["proposal"]
    assert isinstance(proposal["recommended_unit_id"], int)
    assert 0 <= proposal["confidence"] <= 100
    assert proposal["reasoning"].strip()
    assert isinstance(proposal["alternatives"], list)


@pytest.mark.covers("FR-AGENT-02-AC2")
def test_FR_AGENT_02_AC2_a_proposal_is_still_made_when_no_resource_is_free(world):
    client, _ = world
    post(client, report(minute=1))
    post(client, report(minute=2))  # both Medical units are now taken
    third = post(client, report(minute=3)).get_json()
    assert third["proposal"] is not None and third["proposal"]["recommended_unit_id"] in (1, 2)


@pytest.mark.covers("FR-AGENT-03-AC1")
def test_FR_AGENT_03_AC1_confident_non_severe_proposals_proceed_without_a_human(world):
    client, db = world
    body = post(client, report(CLEAR)).get_json()
    assert body["decision"]["final_status"] == "approved" and body["decision"]["decided_by"] == "auto"
    assert query(db, "SELECT status FROM units WHERE id = ?", (body["reservation"]["unit_id"],))[0]["status"] == "assigned"


@pytest.mark.covers("FR-AGENT-03-AC2")
def test_FR_AGENT_03_AC2_low_confidence_or_severe_proposals_wait_for_a_dispatcher(world):
    client, db = world
    low = post(client, report(VAGUE, minute=1)).get_json()  # confidence 40
    severe = post(client, report(SEVERE, minute=2)).get_json()  # confidence 95 but Severe
    for body in (low, severe):
        assert body["decision"]["held_for_human"] is True
    assert query(db, "SELECT id FROM units WHERE status = 'assigned'") == []  # nothing dispatched yet
    approved = client.post(f"/proposals/{low['proposal']['proposal_id']}/decision", json={"decision": "approve"})
    assert approved.status_code == 200 and approved.get_json()["decided_by"] != "auto"
    assert len(query(db, "SELECT id FROM units WHERE status = 'assigned'")) == 1  # only after a person decided


# ---- FR-RES-01 .. 02 ----------------------------------------------------------------------


@pytest.mark.covers("FR-RES-01-AC1")
def test_FR_RES_01_AC1_an_approved_proposal_assigns_the_unit_and_confirms_a_responder(world):
    client, db = world
    body = post(client, report()).get_json()
    unit = body["reservation"]["unit_id"]
    assert query(db, "SELECT status FROM units WHERE id = ?", (unit,))[0]["status"] == "assigned"
    assert query(db, "SELECT unit_id FROM notifications WHERE assignment_id = ?", (body["proposal"]["proposal_id"],)) == [
        {"unit_id": unit}
    ]


@pytest.mark.covers("FR-RES-01-AC2")
@pytest.mark.defect("DEF-013")
def test_FR_RES_01_AC2_a_lost_unit_gets_a_second_path_when_a_dispatcher_approves(world):
    client, db = world
    body = post(client, report(VAGUE)).get_json()  # held, unit reserved
    pid, held_unit = body["proposal"]["proposal_id"], body["reservation"]["unit_id"]
    conn = sqlite3.connect(db)  # the unit becomes unavailable before the dispatcher decides
    conn.execute(
        "UPDATE units SET status = 'out_of_service', reserved_by_proposal_id = NULL, reserved_at = NULL, "
        "released_expected_by = NULL WHERE id = ?",
        (held_unit,),
    )
    conn.commit()
    conn.close()

    resp = client.post(f"/proposals/{pid}/decision", json={"decision": "approve"})

    assert resp.status_code == 200  # a second path to a responder, not an error
    assigned = query(db, "SELECT id FROM units WHERE status = 'assigned'")
    assert assigned and assigned[0]["id"] != held_unit


@pytest.mark.covers("FR-RES-02-AC1")
def test_FR_RES_02_AC1_an_override_logs_who_when_why_the_original_choice_and_the_elapsed_time(world):
    client, db = world
    body = post(client, report(VAGUE)).get_json()
    pid = body["proposal"]["proposal_id"]
    client.post(f"/proposals/{pid}/decision", json={"decision": "approve"})
    other = 2 if body["reservation"]["unit_id"] == 1 else 1

    resp = client.post(f"/assignments/{pid}/override", json={"new_unit_id": other, "reason": "closer to the scene"})

    assert resp.status_code == 200
    row = query(db, "SELECT * FROM dispatcher_overrides")[0]
    assert row["dispatcher_account_id"] and row["overridden_at"] and row["reason"] == "closer to the scene"
    assert row["original_agent_choice_unit_id"] == body["reservation"]["unit_id"]
    assert resp.get_json()["elapsed_seconds_escalation_to_approval"] is not None


@pytest.mark.covers("FR-RES-02-AC2")
def test_FR_RES_02_AC2_an_override_without_a_reason_is_rejected(world):
    client, db = world
    body = post(client, report()).get_json()
    pid = body["proposal"]["proposal_id"]
    other = 2 if body["reservation"]["unit_id"] == 1 else 1
    for reason in (None, "", "   "):
        resp = client.post(f"/assignments/{pid}/override", json={"new_unit_id": other, "reason": reason})
        assert resp.status_code == 400 and resp.get_json()["error"]["code"] == "REASON_REQUIRED"
    assert query(db, "SELECT id FROM dispatcher_overrides") == []


@pytest.mark.covers("FR-RES-02-AC3")
def test_FR_RES_02_AC3_the_dispatcher_can_expand_on_an_override_later_in_the_same_log_entry(world):
    client, db = world
    body = post(client, report()).get_json()
    pid = body["proposal"]["proposal_id"]
    other = 2 if body["reservation"]["unit_id"] == 1 else 1
    oid = client.post(f"/assignments/{pid}/override", json={"new_unit_id": other, "reason": "short"}).get_json()["override_id"]

    resp = client.post(f"/overrides/{oid}/follow-up", json={"text": "the longer explanation"})

    assert resp.status_code == 200
    assert [f["text"] for f in resp.get_json()["follow_ups"]] == ["the longer explanation"]
    assert len(query(db, "SELECT id FROM dispatcher_overrides")) == 1  # still one entry


# ---- FR-ALERT-01, FR-AUDIT-01 .. 02, FR-SIM-01 ---------------------------------------------


@pytest.mark.covers("FR-ALERT-01-AC1")
def test_FR_ALERT_01_AC1_the_responder_is_notified_within_ten_seconds_of_the_assignment(world):
    client, db = world
    body = post(client, report()).get_json()
    decided = datetime.fromisoformat(query(db, "SELECT decided_at FROM agent_proposals")[0]["decided_at"])
    sent = datetime.fromisoformat(body["notification"]["sent_at"])
    assert 0 <= (sent - decided).total_seconds() <= 10
    assert decided.tzinfo is UTC or decided.utcoffset().total_seconds() == 0


@pytest.mark.covers("FR-AUDIT-01-AC1")
@pytest.mark.defect("DEF-014")
def test_FR_AUDIT_01_AC1_the_proposal_log_includes_the_input_data_and_the_confidence(world):
    client, db = world
    post(client, report(CLEAR))
    entry = query(db, "SELECT * FROM agent_proposals")[0]
    assert entry["confidence"] == 95
    logged = json.dumps(entry)  # the proposal's own log entry, not a join to a row that can be purged or changed
    assert "4th & Main St" in logged and CLEAR in logged


@pytest.mark.covers("FR-AUDIT-02-AC1")
def test_FR_AUDIT_02_AC1_an_override_is_logged_with_who_when_and_the_original_proposal(world):
    client, db = world
    body = post(client, report()).get_json()
    pid = body["proposal"]["proposal_id"]
    other = 2 if body["reservation"]["unit_id"] == 1 else 1
    client.post(f"/assignments/{pid}/override", json={"new_unit_id": other, "reason": "why"})
    row = query(db, "SELECT * FROM dispatcher_overrides")[0]
    assert row["dispatcher_account_id"] and row["overridden_at"]
    assert row["assignment_id"] == pid  # points at the original agent proposal, which is kept
    assert query(db, "SELECT recommended_unit_id FROM agent_proposals WHERE id = ?", (pid,))[0]["recommended_unit_id"] == (
        row["original_agent_choice_unit_id"]
    )


@pytest.mark.covers("FR-AUDIT-02-AC2")
def test_FR_AUDIT_02_AC2_a_logged_override_can_only_be_added_to_never_taken_away(world):
    client, db = world
    body = post(client, report()).get_json()
    pid = body["proposal"]["proposal_id"]
    other = 2 if body["reservation"]["unit_id"] == 1 else 1
    oid = client.post(f"/assignments/{pid}/override", json={"new_unit_id": other, "reason": "original reason"}).get_json()["override_id"]
    client.post(f"/overrides/{oid}/follow-up", json={"text": "an addition"})

    conn = sqlite3.connect(db)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE dispatcher_overrides SET reason = 'rewritten' WHERE id = ?", (oid,))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE override_follow_ups SET text = 'rewritten' WHERE override_id = ?", (oid,))
    conn.close()
    assert query(db, "SELECT reason FROM dispatcher_overrides")[0]["reason"] == "original reason"
    assert len(query(db, "SELECT id FROM override_follow_ups")) == 1  # additions are kept


@pytest.mark.covers("FR-SIM-01-AC1")
def test_FR_SIM_01_AC1_the_same_scenario_three_times_gives_the_same_confidence(tmp_path, monkeypatch):
    confidences = []
    for run in range(3):
        db_path = tmp_path / f"run{run}.sqlite"
        monkeypatch.setenv("DB_PATH", str(db_path))
        conn = sqlite3.connect(db_path)
        for path in sorted(glob.glob(str(REPO / "migrations" / "*.sql"))):
            conn.executescript(Path(path).read_text(encoding="utf-8"))
        conn.executescript((REPO / "seed" / "iteration-1.sql").read_text(encoding="utf-8"))
        conn.close()
        from src.web_ui.app import create_app

        app = create_app()
        app.testing = False
        with app.test_client() as client:
            run_scores = [post(client, report(t, minute=i)).get_json()["proposal"]["confidence"] for i, t in enumerate((CLEAR, VAGUE))]
        confidences.append(run_scores)
    assert confidences[0] == confidences[1] == confidences[2]


# ---- non-functional criteria that can be checked end to end ---------------------------------


@pytest.mark.covers("NFR-SEC-01-AC1", "FR-INFER-01-AC1")
def test_NFR_SEC_01_AC1_a_full_scenario_runs_with_outbound_network_blocked_and_calls_no_external_host(world, monkeypatch):
    import socket

    attempts = []
    real_connect = socket.socket.connect

    def watch(self, address):
        host = address[0] if isinstance(address, tuple) else str(address)
        attempts.append(host)
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise OSError("outbound network blocked for this test")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", watch)
    client, _ = world
    codes = [
        post(client, report(CLEAR, 1)).status_code,
        post(client, report(VAGUE, 2)).status_code,
        client.post("/proposals/2/decision", json={"decision": "approve"}).status_code,
        post(client, report(SEVERE, 3)).status_code,
    ]
    assert codes == [201, 201, 200, 409]  # the scenario completes (the 409 is the intended "no unit left")
    assert [a for a in attempts if a not in ("127.0.0.1", "localhost", "::1")] == []  # zero external hosts


def test_the_source_imports_no_network_client_library():
    """Supports FR-INFER-01 and NFR-SEC-01 from the other side: nothing in src/ could call out."""
    forbidden = re.compile(r"^\s*(import|from)\s+(requests|httpx|aiohttp|urllib\.request|http\.client|socket|ftplib|smtplib)\b", re.MULTILINE)
    offenders = [str(p.relative_to(REPO)) for p in (REPO / "src").rglob("*.py") if forbidden.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


@pytest.mark.covers("NFR-SEC-04-AC1")
def test_NFR_SEC_04_AC1_the_secret_scan_finds_nothing_in_this_repo_and_catches_a_planted_key(tmp_path):
    clean = subprocess.run([sys.executable, str(REPO / "tools" / "secrets_scan.py")], check=False, cwd=REPO, capture_output=True, text=True)
    assert clean.returncode == 0, clean.stdout

    repo = tmp_path / "planted"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    fake_key = "sk-" + "A1b2" * 6  # built at run time, so this file does not itself look like a leaked key
    (repo / "config.txt").write_text(f"service_key = {fake_key}\n", encoding="utf-8")
    subprocess.run(["git", "add", "config.txt"], cwd=repo, check=True)
    planted = subprocess.run([sys.executable, str(REPO / "tools" / "secrets_scan.py")], check=False, cwd=repo, capture_output=True, text=True)
    assert planted.returncode != 0


# ---- FR-AUTH-01 (a Should requirement, but a real finding): who may approve? -----------------------------


@pytest.mark.covers("FR-AUTH-01-AC2")
@pytest.mark.defect("DEF-018")
@pytest.mark.xfail(strict=True, reason="open defect DEF-018: there is no login, so an unauthenticated caller can approve")
def test_FR_AUTH_01_AC2_an_unauthenticated_caller_cannot_approve(world):
    client, _ = world
    held = post(client, report(VAGUE)).get_json()
    resp = client.post(f"/proposals/{held['proposal']['proposal_id']}/decision", json={"decision": "approve"})
    assert resp.status_code in (401, 403)
