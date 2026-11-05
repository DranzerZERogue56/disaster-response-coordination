"""Intake Gateway (docs/architecture.md §4) — the component that validates
and queues incoming incident reports.

This walking skeleton implements the real validate-and-insert path behind
Submit Incident Report (architecture.md §5, FR-INTAKE-01, FR-INTAKE-02).
Duplicate detection (FR-INTAKE-03) and the offline queue are stubbed —
see docs/skeleton-trace.md for what's real this week and what isn't.
"""
from collections.abc import Mapping
from datetime import UTC, datetime

REQUIRED_FIELDS = ("location", "severity_raw", "timestamp_reported", "reporting_unit")


class ValidationError(Exception):
    """One or more fields are missing (FIELD_MISSING) or improperly filled (FIELD_INVALID).
    `fields` lists every bad field, top-down in the order of the report form (FR-INTAKE-02)."""

    def __init__(self, fields, code="FIELD_MISSING"):
        self.fields = list(fields)
        self.missing = self.fields  # older name, still used by callers and tests
        self.code = code
        super().__init__(f"{code}: " + ", ".join(self.fields))


class InvalidBody(Exception):
    """The request body is not a JSON object (for example a list or a bare string)."""


class InvalidTimestamp(Exception):
    """timestamp_reported is not an ISO 8601 date and time."""


def normalize_timestamp(value):
    """Return the time as UTC ISO 8601, so ordering by the stored text is
    ordering by time even when reporters send different offsets. A time with
    no offset is taken to be UTC."""
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise InvalidTimestamp(f"timestamp_reported {value!r} is not an ISO 8601 time") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat()


def submit_report(conn, scenario_run_id, fields, queued=False):
    if not isinstance(fields, Mapping):
        raise InvalidBody("The report must be sent as a JSON object, for example {\"location\": ...}")
    missing, invalid = [], []
    for name in REQUIRED_FIELDS:
        value = fields.get(name)
        if value is None or value == "":
            missing.append(name)
        elif not isinstance(value, str) or not value.strip():
            invalid.append(name)  # a number, list, object, boolean, or only whitespace
    description = fields.get("description")
    if description is not None and not isinstance(description, str):
        invalid.append("description")
    bad = [name for name in (*REQUIRED_FIELDS, "description") if name in missing or name in invalid]
    if bad:
        raise ValidationError(bad, "FIELD_MISSING" if missing else "FIELD_INVALID")
    reported = normalize_timestamp(fields["timestamp_reported"])

    received_at = datetime.now(UTC).isoformat()
    cur = conn.execute(
        """
        INSERT INTO incident_reports
            (scenario_run_id, location, severity_raw, timestamp_reported,
             reporting_unit, description, status, received_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            scenario_run_id,
            fields["location"],
            fields["severity_raw"],
            reported,
            fields["reporting_unit"],
            fields.get("description"),
            "queued" if queued else "created",
            received_at,
        ),
    )
    conn.commit()
    return {
        "report_id": cur.lastrowid,
        "status": "queued" if queued else "created",
        "received_at": received_at,
    }


def list_reports(conn, scenario_run_id):
    rows = conn.execute(
        "SELECT id, location, severity_raw, reporting_unit, status, received_at "
        "FROM incident_reports WHERE scenario_run_id = ? ORDER BY id DESC",
        (scenario_run_id,),
    ).fetchall()
    return [dict(r) for r in rows]
