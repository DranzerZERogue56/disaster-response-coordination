"""Offline queue for the Intake Gateway (docs/architecture.md section 5) —
Milestone 10, slice 6.

Serves FR-INTAKE-01 and NFR-REL-03: while the network is down, a submitted
report is saved with status 'queued' instead of being lost. When the network
comes back, queued reports are released and processed in timestamp order,
oldest first, so a burst of them cannot arrive all at once in a random order.

The "network" here is the design's connectivity flag, a switch in memory
(POST /connectivity). The queue itself is the incident_reports table, so
queued reports survive a restart; only the switch resets (to connected).

Not decided by the spec: a maximum queue size (open question OQ-1), so there
is none.
"""
import threading

_lock = threading.Lock()
_connected = True


def is_connected():
    with _lock:
        return _connected


def set_connected(value):
    global _connected
    with _lock:
        _connected = bool(value)


def queued_report_ids(conn):
    """Queued reports, oldest reported first (ties broken by arrival)."""
    return [
        r["id"]
        for r in conn.execute(
            "SELECT id FROM incident_reports WHERE status = 'queued' "
            "ORDER BY timestamp_reported, id"
        ).fetchall()
    ]


def release_queued(conn, report_id):
    """Turn one queued report into a normal created one. False if it was not
    queued (already released), so draining twice never processes a report twice."""
    cur = conn.execute(
        "UPDATE incident_reports SET status = 'created' WHERE id = ? AND status = 'queued'",
        (report_id,),
    )
    conn.commit()
    return cur.rowcount == 1


def drain_queue(conn, process):
    """Release and process every queued report in timestamp order.

    `process(conn, report_id)` does the real work and returns a summary. One
    report failing to find a unit does not stop the rest, and none is lost:
    a released report stays 'created' even if processing it reports an error.
    """
    summaries = []
    for report_id in queued_report_ids(conn):
        if release_queued(conn, report_id):
            summaries.append(process(conn, report_id))
    return summaries
