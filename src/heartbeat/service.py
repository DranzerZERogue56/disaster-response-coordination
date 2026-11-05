"""Node Heartbeats (docs/architecture.md section 5), Milestone 11 / FR-DEGRADE-01.

`heartbeat` records that a node is alive. `check_nodes` is the watcher: a node silent for `interval_s * misses`
seconds (default 10 x 3 = 30) is flagged `not_responding`, one alert is written, and one notice goes to every
other agent that is still alive plus one to a human. Polling is idempotent: a node that is already flagged does
not raise a second alert.

When a flagged node sends a heartbeat again, its alert is marked as a late recovery and the earlier notices
are updated to say so at once, but the node stays `not_responding`: it becomes `recovered` only when a human
confirms (`confirm_recovery`), because the schema forbids `recovered` without a confirming dispatcher and
somebody has to check that the interruption did not change any information. If a node that resumed goes
silent again before anyone confirms, that is a new episode with a new alert.
"""
from datetime import UTC, datetime, timedelta

from src.unit_registry.broadcast import deliver_cached

INTERVAL_SECONDS = 10
MISSES = 3


class HeartbeatError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _now(now):
    return now or datetime.now(UTC)


def _moment(text):
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _open_alert(conn, node_id):
    """The node's latest alert that has not yet been confirmed by a human, or None."""
    return conn.execute(
        "SELECT * FROM node_alerts WHERE node_id = ? AND confirmed_at IS NULL ORDER BY id DESC LIMIT 1", (node_id,)
    ).fetchone()


def heartbeat(conn, node_id, now=None):
    """Record that a node is alive. Returns {node_id, last_heartbeat_at, resumed_after_alert}. A heartbeat older
    than the one already recorded is ignored. Raises LookupError for an unknown node."""
    moment = _now(now)
    node = conn.execute("SELECT status, last_heartbeat_at FROM agent_nodes WHERE id = ?", (node_id,)).fetchone()
    if node is None:
        raise LookupError(f"No agent node with id {node_id}")
    if moment <= _moment(node["last_heartbeat_at"]):
        return {"node_id": node_id, "last_heartbeat_at": node["last_heartbeat_at"], "resumed_after_alert": False}

    stamp = moment.isoformat()
    conn.execute("UPDATE agent_nodes SET last_heartbeat_at = ? WHERE id = ?", (stamp, node_id))
    resumed = False
    if node["status"] == "not_responding":
        deliver_cached(conn, node_id, stamp)  # the updates it missed while down (FR-RES-03-AC2)
        alert = _open_alert(conn, node_id)
        if alert is not None and alert["recovered_at"] is None:
            conn.execute("UPDATE node_alerts SET recovered_at = ? WHERE id = ?", (stamp, alert["id"]))
            conn.execute("UPDATE node_notices SET late_recovery = 1, updated_at = ? WHERE alert_id = ?", (stamp, alert["id"]))
            resumed = True
    conn.commit()
    return {"node_id": node_id, "last_heartbeat_at": stamp, "resumed_after_alert": resumed}


def check_nodes(conn, now=None, interval_s=INTERVAL_SECONDS, misses=MISSES):
    """Flag every node silent for `interval_s * misses` seconds and notify the others and a human. Returns one
    dict per newly flagged node ({node_id, alert_id, silent_seconds}); nothing already flagged is flagged again."""
    if interval_s <= 0 or misses <= 0:
        raise ValueError("interval_s and misses must both be above zero")
    moment = _now(now)
    limit = timedelta(seconds=interval_s * misses)

    silent = []
    for node in conn.execute("SELECT id, role_type, status, last_heartbeat_at FROM agent_nodes ORDER BY id").fetchall():
        quiet_for = moment - _moment(node["last_heartbeat_at"])
        if quiet_for < limit:
            continue
        if node["status"] in ("alive", "recovered"):
            silent.append((node, quiet_for))
        elif node["status"] == "not_responding":
            alert = _open_alert(conn, node["id"])
            if alert is not None and alert["recovered_at"] is not None:
                silent.append((node, quiet_for))  # resumed, awaiting a human, and then went quiet again

    silent_ids = {node["id"] for node, _ in silent}
    survivors = [
        r["id"]
        for r in conn.execute("SELECT id FROM agent_nodes WHERE status IN ('alive', 'recovered') ORDER BY id")
        if r["id"] not in silent_ids
    ]
    stamp = moment.isoformat()
    flagged = []
    for node, quiet_for in silent:
        seconds = quiet_for.total_seconds()
        alert_id = conn.execute(
            "INSERT INTO node_alerts (node_id, raised_at, silent_seconds) VALUES (?, ?, ?)", (node["id"], stamp, seconds)
        ).lastrowid
        conn.execute("UPDATE agent_nodes SET status = 'not_responding' WHERE id = ?", (node["id"],))
        text = f"Node {node['id']} ({node['role_type']}) has not responded for {seconds:.0f} seconds."
        for other in survivors:
            conn.execute(
                "INSERT INTO node_notices (alert_id, audience, to_node_id, message, created_at) VALUES (?, 'agent', ?, ?, ?)",
                (alert_id, other, text, stamp),
            )
        conn.execute(
            "INSERT INTO node_notices (alert_id, audience, to_node_id, message, created_at) VALUES (?, 'human', NULL, ?, ?)",
            (alert_id, text + " A dispatcher must check its information when it returns.", stamp),
        )
        flagged.append({"node_id": node["id"], "alert_id": alert_id, "silent_seconds": seconds})
    conn.commit()
    return flagged


def confirm_recovery(conn, node_id, dispatcher_id, now=None):
    """A dispatcher confirms the interruption did not affect any information; only this makes the node
    `recovered`. Raises HeartbeatError: NOT_A_DISPATCHER, NODE_NOT_FLAGGED, NODE_NOT_RESUMED."""
    account = conn.execute("SELECT role FROM dispatcher_accounts WHERE id = ?", (dispatcher_id,)).fetchone()
    if account is None or account["role"] not in ("admin", "dispatcher"):
        raise HeartbeatError("NOT_A_DISPATCHER", "Only a dispatcher can confirm a node's recovery.")
    node = conn.execute("SELECT status FROM agent_nodes WHERE id = ?", (node_id,)).fetchone()
    if node is None:
        raise LookupError(f"No agent node with id {node_id}")
    alert = _open_alert(conn, node_id)
    if node["status"] != "not_responding" or alert is None:
        raise HeartbeatError("NODE_NOT_FLAGGED", f"Node {node_id} is not flagged as not responding.")
    if alert["recovered_at"] is None:
        raise HeartbeatError("NODE_NOT_RESUMED", f"Node {node_id} has not started responding again.")

    stamp = _now(now).isoformat()
    conn.execute(
        "UPDATE node_alerts SET confirmed_at = ?, confirmed_by = ? "
        "WHERE node_id = ? AND confirmed_at IS NULL AND recovered_at IS NOT NULL",
        (stamp, dispatcher_id, node_id),
    )
    conn.execute("UPDATE agent_nodes SET status = 'recovered', recovered_confirmed_by = ? WHERE id = ?", (dispatcher_id, node_id))
    deliver_cached(conn, node_id, stamp)  # nothing cached may be left behind once the node is trusted again
    conn.commit()
    return {"node_id": node_id, "status": "recovered", "confirmed_by": dispatcher_id, "confirmed_at": stamp}
