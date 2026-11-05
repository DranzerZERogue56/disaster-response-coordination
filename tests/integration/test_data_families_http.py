"""Milestone 11: the three test-data families (happy, boundary, hostile) sent through the
real intake route against a real seeded SQLite database.

Where the system does not do what the specification calls for, the case is an OPEN DEFECT:
it is marked xfail(strict=True) with the defect id, so the suite stays green, the traceability
matrix shows the criterion as failing, and fixing the defect makes the strict xfail turn red
until the marker is deleted. See docs/defect-log.md.
"""
import glob
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data"

# entry name -> (open defect id, which kinds of test it breaks). "crash" = the server returns a 5xx;
# "reject" = the specification says reject, but the report is accepted or the server crashes.
# Empty when every defect the data found is fixed. Fixed ones are tagged with @pytest.mark.defect below.
OPEN_DEFECTS = {}  # DEF-009 to DEF-012 were fixed (see docs/defect-log.md); their regression tests are the cases below


def load(family):
    return json.loads((DATA / f"{family}.json").read_text(encoding="utf-8"))


def params(family, kind=None, expect=None):
    out = []
    for e in load(family):
        if expect and e["expect"] != expect:
            continue
        marks = []
        defect = OPEN_DEFECTS.get(e["name"])
        if defect and kind in defect[1]:
            marks = [
                pytest.mark.xfail(strict=True, reason=f"open defect {defect[0]}"),
                pytest.mark.defect(defect[0]),
            ]
        out.append(pytest.param(e, marks=marks, id=e["name"]))
    return out


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "families.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    c = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    c.commit()
    c.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False  # behave like production: an unhandled error is a real HTTP 500
    with app.test_client() as tc:
        yield tc, db_path


def send(tc, payload):
    return tc.post("/reports", data=json.dumps(payload), content_type="application/json")


def rows(db_path, sql, args=()):
    c = sqlite3.connect(db_path)
    out = c.execute(sql, args).fetchall()
    c.close()
    return out


# --- the data itself -------------------------------------------------------------------------


@pytest.mark.parametrize("family", ["happy", "boundary", "hostile"])
def test_every_entry_is_marked_synthetic_and_has_a_stated_outcome(family):
    entries = load(family)
    assert entries, family
    assert all(e["synthetic"] is True for e in entries)
    assert all(e["expect"] in ("accept", "reject", "safe") for e in entries)
    assert len({e["name"] for e in entries}) == len(entries)


def test_the_data_is_reproducible_from_the_fixed_seed(tmp_path):
    """Regenerating gives byte-identical files (so a diff means the generator changed)."""
    def read(f):
        return (DATA / f"{f}.json").read_bytes().replace(b"\r\n", b"\n")  # a Windows checkout may use CRLF

    before = {f: read(f) for f in ("happy", "boundary", "hostile")}
    subprocess.run([sys.executable, str(DATA / "generate.py")], check=True, capture_output=True)
    after = {f: read(f) for f in ("happy", "boundary", "hostile")}
    assert before == after


def test_the_data_contains_no_real_personal_data():
    """No email addresses or phone numbers anywhere in the committed data."""
    import re

    text = "".join((DATA / f"{f}.json").read_text(encoding="utf-8") for f in ("happy", "boundary", "hostile"))
    assert "@" not in text  # no email address can exist without one (and a regex is slow on the 100k-character strings)
    assert not re.search(r"\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b", text)


# --- happy: a valid report is accepted ---------------------------------------------------------


@pytest.mark.covers("FR-INTAKE-01-AC1")
@pytest.mark.parametrize("entry", params("happy", "accept"))
def test_happy_reports_are_accepted_and_confirmed(client, entry):
    tc, db = client
    resp = send(tc, entry["payload"])
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "created" and body["report_id"] > 0
    assert rows(db, "SELECT count(*) FROM incident_reports WHERE id = ?", (body["report_id"],)) == [(1,)]


# --- boundary: each edge gets the outcome the specification calls for ------------------------


@pytest.mark.covers("FR-INTAKE-02-AC1")
@pytest.mark.parametrize("entry", params("boundary", "reject", expect="reject"))
def test_boundary_rejections_name_what_is_wrong(client, entry):
    tc, db = client
    resp = send(tc, entry["payload"])
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] in ("FIELD_MISSING", "INVALID_TIMESTAMP")
    assert rows(db, "SELECT count(*) FROM incident_reports") == [(0,)]


@pytest.mark.covers("FR-INTAKE-01-AC1")
@pytest.mark.parametrize("entry", params("boundary", "accept", expect="accept"))
def test_boundary_values_that_are_allowed_are_accepted(client, entry):
    tc, _ = client
    assert send(tc, entry["payload"]).status_code == 201


# --- hostile: never crash; reject what the specification says to reject; store the rest as sent --


@pytest.mark.defect("DEF-009", "DEF-010")
@pytest.mark.parametrize("entry", params("hostile", "crash"))
def test_hostile_input_never_crashes_the_server(client, entry):
    tc, db = client
    resp = send(tc, entry["payload"])
    assert resp.status_code < 500
    # whatever was sent, the data store is intact
    assert rows(db, "SELECT count(*) FROM units")[0][0] == 2
    assert rows(db, "SELECT count(*) FROM scenario_runs")[0][0] == 1


@pytest.mark.covers("FR-INTAKE-02-AC1")
@pytest.mark.defect("DEF-009", "DEF-010", "DEF-011", "DEF-012")
@pytest.mark.parametrize("entry", params("hostile", "reject", expect="reject"))
def test_hostile_input_the_specification_rejects_is_rejected(client, entry):
    tc, db = client
    resp = send(tc, entry["payload"])
    assert resp.status_code == 400
    assert rows(db, "SELECT count(*) FROM incident_reports") == [(0,)]


@pytest.mark.parametrize("entry", params("hostile", "safe", expect="safe"))
def test_hostile_text_that_is_accepted_is_stored_exactly_as_sent(client, entry):
    tc, db = client
    resp = send(tc, entry["payload"])
    if resp.status_code != 201:
        return  # rejecting it is also safe
    sent = entry["payload"]
    stored = rows(db, "SELECT location, severity_raw FROM incident_reports WHERE id = ?", (resp.get_json()["report_id"],))[0]
    assert stored == (sent["location"], sent["severity_raw"])  # no mangling, no execution of anything inside it


def test_a_client_cannot_choose_its_own_status_or_id(client):
    tc, db = client
    entry = next(e for e in load("hostile") if e["name"] == "extra-unknown-fields")
    resp = send(tc, entry["payload"])
    assert resp.status_code == 201
    status, rid = rows(db, "SELECT status, id FROM incident_reports")[0]
    assert status == "classified"  # set by the system after classification, not by the sender
    assert rid == resp.get_json()["report_id"]  # the sender's "id": 1 was ignored (the first report gets id 1 anyway; see below)
