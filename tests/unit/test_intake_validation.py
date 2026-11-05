"""Regression tests for DEF-009 to DEF-012 (found by the hostile test data in Milestone 11) and the
boundary cases of intake validation (FR-INTAKE-02)."""
import glob
import sqlite3

import pytest

from src.intake_gateway.service import InvalidBody, ValidationError, submit_report

GOOD = {
    "location": "4th & Main St",
    "severity_raw": "chest pain",
    "timestamp_reported": "2026-11-01T12:00:00+00:00",
    "reporting_unit": "field-unit-7",
}


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "validation.sqlite")
    c.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())
    yield c
    c.close()


def stored(conn):
    return conn.execute("SELECT count(*) FROM incident_reports").fetchone()[0]


@pytest.mark.covers("FR-INTAKE-02-AC1")
@pytest.mark.defect("DEF-009")
@pytest.mark.parametrize("body", [[1, 2, 3], "just a string", 42, True])
def test_a_body_that_is_not_a_json_object_is_refused_not_crashed(conn, body):
    with pytest.raises(InvalidBody):
        submit_report(conn, 1, body)
    assert stored(conn) == 0


@pytest.mark.covers("FR-INTAKE-02-AC1")
@pytest.mark.defect("DEF-010")
@pytest.mark.parametrize("bad", [["chest pain"], {"street": "x"}, [[["deep"]]]])
def test_a_list_or_object_where_text_belongs_is_invalid_not_a_crash(conn, bad):
    with pytest.raises(ValidationError) as exc:
        submit_report(conn, 1, {**GOOD, "severity_raw": bad})
    assert exc.value.code == "FIELD_INVALID" and exc.value.fields == ["severity_raw"]
    assert stored(conn) == 0


@pytest.mark.covers("FR-INTAKE-02-AC1")
@pytest.mark.defect("DEF-011")
@pytest.mark.parametrize("blank", ["   ", "\t", " \n ", " "])
def test_whitespace_only_text_is_invalid(conn, blank):
    with pytest.raises(ValidationError) as exc:
        submit_report(conn, 1, {**GOOD, "location": blank})
    assert exc.value.code == "FIELD_INVALID" and exc.value.fields == ["location"]
    assert stored(conn) == 0


@pytest.mark.covers("FR-INTAKE-02-AC1")
@pytest.mark.defect("DEF-012")
@pytest.mark.parametrize("bad", [123, 4.5, True, False, 0])
def test_a_number_or_boolean_is_not_accepted_as_text(conn, bad):
    with pytest.raises(ValidationError) as exc:
        submit_report(conn, 1, {**GOOD, "reporting_unit": bad})
    assert exc.value.code == "FIELD_INVALID" and exc.value.fields == ["reporting_unit"]
    assert stored(conn) == 0


@pytest.mark.covers("FR-INTAKE-02-AC2")
def test_every_bad_field_is_reported_together_in_form_order(conn):
    with pytest.raises(ValidationError) as exc:
        submit_report(conn, 1, {"location": "  ", "severity_raw": "", "timestamp_reported": 5})
    # location: only whitespace (invalid); severity_raw: empty (missing); timestamp_reported: a number
    # (invalid); reporting_unit: absent (missing). All four, in form order, one response.
    assert exc.value.fields == ["location", "severity_raw", "timestamp_reported", "reporting_unit"]
    assert exc.value.code == "FIELD_MISSING"  # at least one is missing


@pytest.mark.covers("FR-INTAKE-02-AC1")
def test_an_optional_description_must_be_text_if_present(conn):
    with pytest.raises(ValidationError) as exc:
        submit_report(conn, 1, {**GOOD, "description": ["not", "text"]})
    assert exc.value.fields == ["description"]
    ok = submit_report(conn, 1, {**GOOD, "description": None})
    assert ok["status"] == "created"
    assert submit_report(conn, 1, {**GOOD, "description": "details"})["status"] == "created"


@pytest.mark.covers("FR-INTAKE-01-AC1")
def test_a_complete_valid_report_is_still_accepted_after_the_stricter_checks(conn):
    result = submit_report(conn, 1, GOOD)
    assert result["status"] == "created" and stored(conn) == 1
