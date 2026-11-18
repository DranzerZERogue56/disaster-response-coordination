"""Inputs that attack the interpreter and the parsers, through the real routes (DEF-033, DEF-034).

None of these may reach the user as an HTTP 500; each must be a clean refusal or be stored as plain data.
"""
import glob
import json
import sqlite3
from pathlib import Path

import pytest

GOOD = {"location": "4th & Main St", "severity_raw": "person fell", "timestamp_reported": "2026-11-01T12:00:00+00:00", "reporting_unit": "u"}
NESTED_LIST = ("[" * 100000 + "]" * 100000).encode()
NESTED_OBJECT = (('{"a":' * 50000) + "1" + ("}" * 50000)).encode()
ROUTES = ["/reports", "/proposals/1/decision", "/assignments/1/override", "/overrides/1/follow-up", "/reconciliations/1/override", "/connectivity"]


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "hostile.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.delenv("AUTH_ENFORCED", raising=False)
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    conn.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, db_path


@pytest.mark.covers("NFR-REL-01-AC1")
@pytest.mark.defect("DEF-033")
@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("body", [NESTED_LIST, NESTED_OBJECT], ids=["nested-list", "nested-object"])
def test_a_deeply_nested_body_is_refused_cleanly_not_a_500(world, route, body):
    client, _ = world
    response = client.post(route, data=body, content_type="application/json")
    assert response.status_code < 500, f"POST {route} answered {response.status_code}"


@pytest.mark.covers("NFR-REL-01-AC1")
@pytest.mark.defect("DEF-034")
def test_a_lone_surrogate_in_a_text_field_is_refused_cleanly_not_a_500(world):
    client, db = world
    body = b'{"location":"\\ud800","severity_raw":"x","timestamp_reported":"2026-11-01T12:00:00+00:00","reporting_unit":"u"}'
    response = client.post("/reports", data=body, content_type="application/json")
    assert response.status_code == 400 and response.get_json()["error"]["code"] == "INVALID_TEXT"
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0] == 0


@pytest.mark.defect("DEF-034")
@pytest.mark.parametrize("route", ["/proposals/1/decision", "/assignments/1/override", "/overrides/1/follow-up"])
def test_a_lone_surrogate_in_any_other_text_field_is_not_a_500_either(world, route):
    client, _ = world
    body = b'{"decision":"\\ud800","reason":"\\ud800","text":"\\ud800","new_unit_id":2}'
    assert client.post(route, data=body, content_type="application/json").status_code < 500


@pytest.mark.parametrize(
    "location",
    ["'; DROP TABLE units; --", "Robert'); DROP TABLE incident_reports;--", "1 OR 1=1", "a\x00b", "<script>alert(1)</script>", "../../etc/passwd", "{{7*7}}", "${jndi:ldap://x}", "%s%s%s%n"],
)
def test_injection_looking_text_is_stored_as_plain_data_and_the_tables_survive(world, location):
    client, db = world
    response = client.post("/reports", data=json.dumps({**GOOD, "location": location}), content_type="application/json")
    assert response.status_code < 500
    check = sqlite3.connect(db)
    assert check.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 2
    assert check.execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0] >= 1
    assert check.execute("SELECT location FROM incident_reports ORDER BY id DESC LIMIT 1").fetchone()[0] == location


@pytest.mark.parametrize("body", [b'{"modified_unit_id": NaN}', b'{"modified_unit_id": Infinity}', b'{"modified_unit_id": ' + b"9" * 5000 + b"}", b'{"decision": "modify", "modified_unit_id": -0.0}', b"\xff\xfe", b"", b"null", b"\"text\""])
def test_numeric_and_encoding_tricks_never_produce_a_500(world, body):
    client, _ = world
    assert client.post("/proposals/1/decision", data=body, content_type="application/json").status_code < 500
