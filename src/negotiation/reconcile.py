"""Reconcile Incident Versions (docs/architecture.md section 5), Milestone 11 / FR-COORD-02.

Two agents can hold different, differently-timestamped pictures of one incident. Every picture is kept as an
`incident_versions` row. The automatic rule: the version with the newest data time is active; equal data
times go to the version recorded later (higher id), so the answer is deterministic and never flips. Older
versions stay as history and are never deleted (only the 24-hour purge removes them).

A dispatcher can override the automatic choice with a written reason. The override is logged with who, when,
why and the original automatic decision, and it stands until genuinely newer data changes what the automatic
rule would pick.
"""
import json
from datetime import UTC, datetime


class ReconcileError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _stamp(now):
    return (now or datetime.now(UTC)).isoformat()


def _moment(text):
    """A data timestamp as a real moment, so different time zones compare correctly. A time with no zone is
    read as UTC."""
    parsed = datetime.fromisoformat(str(text))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def record_version(conn, report_id, agent_node_id, data, data_timestamp, now=None):
    """Store one agent's picture of an incident (not yet active). Returns the version id.
    Raises TypeError for data that is not an object, ValueError for a timestamp that cannot be read."""
    if not isinstance(data, dict):
        raise TypeError("data must be an object")
    _moment(data_timestamp)  # raises ValueError if unreadable
    cur = conn.execute(
        "INSERT INTO incident_versions (report_id, agent_node_id, data, data_timestamp, active, recorded_at) "
        "VALUES (?, ?, ?, ?, 0, ?)",
        (report_id, agent_node_id, json.dumps(data), str(data_timestamp), _stamp(now)),
    )
    conn.commit()
    return cur.lastrowid


def _automatic_choice(versions):
    return max(versions, key=lambda v: (_moment(v["data_timestamp"]), v["id"]))


def _load(conn, report_id):
    if conn.execute("SELECT 1 FROM incident_reports WHERE id = ?", (report_id,)).fetchone() is None:
        raise LookupError(f"No incident report with id {report_id}")
    versions = [dict(r) for r in conn.execute("SELECT * FROM incident_versions WHERE report_id = ?", (report_id,))]
    active = next((v for v in versions if v["active"]), None)
    last = conn.execute(
        "SELECT * FROM reconciliation_log WHERE report_id = ? ORDER BY id DESC LIMIT 1", (report_id,)
    ).fetchone()
    return versions, active, last


def _activate(conn, report_id, version_id, stamp):
    conn.execute(
        "UPDATE incident_versions SET active = 0, superseded_at = ? WHERE report_id = ? AND active = 1",
        (stamp, report_id),
    )
    conn.execute("UPDATE incident_versions SET active = 1, superseded_at = NULL WHERE id = ?", (version_id,))


def reconcile(conn, report_id, now=None):
    """Apply the automatic rule. Returns {active_version_id, changed}. Logs only when the active version
    changes. A standing human override is left alone until newer data changes the automatic choice."""
    versions, active, last = _load(conn, report_id)
    if not versions:
        return {"active_version_id": None, "changed": False}
    choice = _automatic_choice(versions)

    if last is not None and last["kind"] == "override" and last["original_version_id"] == choice["id"]:
        return {"active_version_id": active["id"] if active else None, "changed": False}
    if active is not None and active["id"] == choice["id"]:
        return {"active_version_id": choice["id"], "changed": False}

    stamp = _stamp(now)
    _activate(conn, report_id, choice["id"], stamp)
    conn.execute(
        "INSERT INTO reconciliation_log (report_id, kind, original_version_id, chosen_version_id, decided_at) "
        "VALUES (?, 'automatic', ?, ?, ?)",
        (report_id, choice["id"], choice["id"], stamp),
    )
    conn.commit()
    return {"active_version_id": choice["id"], "changed": True}


def override_reconciliation(conn, report_id, version_id, reason, dispatcher_id, now=None):
    """A dispatcher picks a different active version, with a reason. Returns {active_version_id, log_id}.
    Raises ReconcileError: REASON_REQUIRED, NOT_A_DISPATCHER, VERSION_NOT_FOUND."""
    if not isinstance(reason, str) or not reason.strip():
        raise ReconcileError("REASON_REQUIRED", "An override needs a written reason.")
    account = conn.execute("SELECT role FROM dispatcher_accounts WHERE id = ?", (dispatcher_id,)).fetchone()
    if account is None or account["role"] not in ("admin", "dispatcher"):
        raise ReconcileError("NOT_A_DISPATCHER", "Only a dispatcher can override a reconciliation.")
    versions, _active, _last = _load(conn, report_id)
    if not any(v["id"] == version_id for v in versions):
        raise ReconcileError("VERSION_NOT_FOUND", f"Version {version_id} does not belong to incident {report_id}.")

    stamp = _stamp(now)
    original = _automatic_choice(versions)
    _activate(conn, report_id, version_id, stamp)
    log_id = conn.execute(
        "INSERT INTO reconciliation_log (report_id, kind, original_version_id, chosen_version_id, decided_by, reason, decided_at) "
        "VALUES (?, 'override', ?, ?, ?, ?, ?)",
        (report_id, original["id"], version_id, dispatcher_id, reason.strip(), stamp),
    ).lastrowid
    conn.commit()
    return {"active_version_id": version_id, "log_id": log_id}
