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


def submit_report(conn, scenario_run_id, fields):
    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        raise ValidationError(missing)

    received_at = datetime.now(UTC).isoformat()
    cur = conn.execute(
        """
        INSERT INTO incident_reports
            (scenario_run_id, location, severity_raw, timestamp_reported,
             reporting_unit, description, status, received_at)
        VALUES (?, ?, ?, ?, ?, ?, 'created', ?)
        """,
        (
            scenario_run_id,
            fields["location"],
            fields["severity_raw"],
            fields["timestamp_reported"],
            fields["reporting_unit"],
            fields.get("description"),
            received_at,
        ),
    )
    conn.commit()
    return {"report_id": cur.lastrowid, "status": "created", "received_at": received_at}


def list_reports(conn, scenario_run_id):
    rows = conn.execute(
        "SELECT id, location, severity_raw, reporting_unit, status, received_at "
        "FROM incident_reports WHERE scenario_run_id = ? ORDER BY id DESC",
        (scenario_run_id,),
    ).fetchall()
    return [dict(r) for r in rows]
