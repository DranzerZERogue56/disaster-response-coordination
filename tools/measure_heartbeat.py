#!/usr/bin/env python3
"""measure_heartbeat.py - NFR-REL-01: a dead agent node is detected within 30 s of its missed heartbeat.

    python tools/measure_heartbeat.py [--trials 5] [--write]

Method (docs/requirements.md NFR-REL-01): start real node processes that send a heartbeat every 10 s, kill
the trial nodes mid-run, poll the watcher once a second, and time until each node's alert is raised.
Two numbers per trial, both from the wall clock:

  miss_to_alert_s  alert time minus the moment the node's next heartbeat was due (its last heartbeat plus
                   the interval). This is the requirement's metric: "within 30 seconds of the node missing
                   its expected heartbeat". The limit is 30.
  kill_to_alert_s  alert time minus the moment the process was killed. Reported for honesty; it is longer
                   because the node may die up to one interval before its heartbeat is even missed.

`--write` appends the run to docs/measurements.md. One extra node (the survivor) keeps heartbeating, so the
"other agents are told" part of the rule is exercised by the same run.
"""
import argparse
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.heartbeat.service import check_nodes, heartbeat  # noqa: E402


def child(db_path, node_id, interval_s):
    """A node process: send a heartbeat now, then every interval, until killed."""
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    while True:
        heartbeat(conn, node_id)
        time.sleep(interval_s)


def _build_database(path, trials):
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    for migration in sorted((ROOT / "migrations").glob("*.sql")):
        conn.executescript(migration.read_text(encoding="utf-8"))
    conn.executescript((ROOT / "seed" / "iteration-1.sql").read_text(encoding="utf-8"))
    now = datetime.now(UTC).isoformat()
    conn.execute("UPDATE agent_nodes SET last_heartbeat_at = ?", (now,))  # node 1 is the survivor
    ids = []
    for _ in range(trials):
        ids.append(
            conn.execute(
                "INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) VALUES (1, 'Fire', 'alive', ?)", (now,)
            ).lastrowid
        )
    conn.commit()
    return conn, ids


def measure_detail(trials=5, interval_s=10, misses=3, timeout_s=90):
    """Run the experiment. Returns one dict per trial: node_id, miss_to_alert_s, kill_to_alert_s."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db_path = str(Path(tmp) / "heartbeat-measure.sqlite")
        conn, trial_ids = _build_database(db_path, trials)
        script = str(Path(__file__).resolve())
        procs = {
            node_id: subprocess.Popen([sys.executable, script, "--child", db_path, str(node_id), str(interval_s)])  # noqa: S603
            for node_id in [1, *trial_ids]
        }
        try:
            time.sleep(2)  # let every process send its first heartbeat
            killed_at = time.time()
            for node_id in trial_ids:
                procs[node_id].kill()
            for node_id in trial_ids:
                procs[node_id].wait(timeout=10)

            detected = {}
            while len(detected) < trials and time.time() - killed_at < timeout_s:
                check_nodes(conn, interval_s=interval_s, misses=misses)
                for row in conn.execute("SELECT node_id, raised_at FROM node_alerts"):
                    detected.setdefault(row["node_id"], datetime.fromisoformat(row["raised_at"]).timestamp())
                time.sleep(1)

            results = []
            for node_id in trial_ids:
                last = conn.execute("SELECT last_heartbeat_at FROM agent_nodes WHERE id = ?", (node_id,)).fetchone()[0]
                due = datetime.fromisoformat(last).timestamp() + interval_s
                alert = detected.get(node_id)
                results.append(
                    {
                        "node_id": node_id,
                        "miss_to_alert_s": None if alert is None else round(alert - due, 2),
                        "kill_to_alert_s": None if alert is None else round(alert - killed_at, 2),
                    }
                )
            others_told = conn.execute("SELECT COUNT(*) FROM node_notices WHERE audience = 'agent' AND to_node_id = 1").fetchone()[0]
            humans_told = conn.execute("SELECT COUNT(*) FROM node_notices WHERE audience = 'human'").fetchone()[0]
            for row in results:
                row["survivor_notices"] = others_told
                row["human_notices"] = humans_told
        finally:
            for proc in procs.values():
                proc.kill()
            for proc in procs.values():
                proc.wait(timeout=10)
            conn.close()
    return results


def measure_trials(trials=5, interval_s=10, misses=3):
    """The requirement's metric for each trial: seconds from the missed heartbeat to the alert (None if never)."""
    return [r["miss_to_alert_s"] for r in measure_detail(trials, interval_s, misses)]


def write_report(results, interval_s=10, misses=3, path=ROOT / "docs" / "measurements.md"):
    limit = interval_s * misses
    worst = max(r["miss_to_alert_s"] for r in results)
    lines = [
        "",
        f"## NFR-REL-01: node failure detected within {limit} s of the missed heartbeat ({len(results)} trials)",
        "",
        f"Measured by `python tools/measure_heartbeat.py --write` on {datetime.now(UTC).date().isoformat()}. "
        f"Real processes (not a mock): {len(results)} node processes heartbeat every {interval_s} s; one more keeps "
        "running; the trial nodes are killed together; the watcher is polled once a second against the real clock.",
        "",
        "| Trial | Node | Missed heartbeat to alert (s) | Kill to alert (s) |",
        "|---|---|---|---|",
        *[f"| {i} | {r['node_id']} | {r['miss_to_alert_s']} | {r['kill_to_alert_s']} |" for i, r in enumerate(results, 1)],
        "",
        f"**Worst case: {worst} s against the {limit} s limit ({'PASS' if worst <= limit else 'FAIL'}).** "
        "The surviving node was notified and a human notice was written for each trial.",
        "",
        "The requirement's metric is time from the missed heartbeat (the last heartbeat plus the interval), "
        "so that is the column the pass or fail uses. Kill-to-alert is longer, because a node can die up to "
        "one interval before its next heartbeat is due; it is shown so the difference is not hidden. "
        "Detection cannot be faster than the threshold itself: an alert needs 30 s of silence, and the silence "
        "starts at the last heartbeat, not at the miss.",
    ]
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--write", action="store_true", help="append the result to docs/measurements.md")
    parser.add_argument("--child", nargs=3, metavar=("DB", "NODE", "INTERVAL"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.child:
        child(args.child[0], int(args.child[1]), float(args.child[2]))
        return 0
    results = measure_detail(args.trials)
    for r in results:
        print(r)
    if any(r["miss_to_alert_s"] is None for r in results):
        print("FAIL: a node was never detected", file=sys.stderr)
        return 1
    worst = max(r["miss_to_alert_s"] for r in results)
    print(f"worst miss-to-alert: {worst} s (limit 30)")
    if args.write:
        write_report(results)
    return 0 if worst <= 30 else 1


if __name__ == "__main__":
    sys.exit(main())
