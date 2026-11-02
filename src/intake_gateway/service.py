"""Intake Gateway (docs/architecture.md §4) — the component that validates
and queues incoming incident reports.

This walking skeleton implements the real validate-and-insert path behind
Submit Incident Report (architecture.md §5, FR-INTAKE-01, FR-INTAKE-02).
Duplicate detection (FR-INTAKE-03) and the offline queue are stubbed —
see docs/skeleton-trace.md for what's real this week and what isn't.
"""
from datetime import UTC, datetime

REQUIRED_FIELDS = ("location", "severity_raw", "timestamp_reported", "reporting_unit")


class ValidationError(Exception):
    def __init__(self, missing):
        self.missing = missing
        super().__init__("FIELD_MISSING: " + ", ".join(missing))


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
    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        raise ValidationError(missing)
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
