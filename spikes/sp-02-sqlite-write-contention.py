#!/usr/bin/env python3
"""SP-02 spike — SQLite write contention on a unit reservation.

Throwaway script for docs/spikes/SP-02-sqlite-write-contention-under-
concurrent-mesa-agents.md. Uses the real migrations/0001-initial.sql
schema (not a toy table) so the result is about our actual design, not
an approximation of it.

For each of 20 trials: create one fresh unit row (status='available'),
then launch 3 OS processes that all race to run the exact UPDATE the
Resource/Unit Registry's reserve() interface (docs/architecture.md §5)
is specified to run:

    UPDATE units SET status='reserved', reserved_by_proposal_id=?
    WHERE id=? AND status='available'

and record each process's own view of whether its write "took" (its
own UPDATE reported 1 row changed). After all 3 finish, re-read the row
to see which proposal_id actually won, and check for: more than one
process believing it won (double-booking), or no process's reservation
landing at all (a lost write).

    python3 spikes/sp-02-sqlite-write-contention.py
"""
import multiprocessing as mp
import os
import sqlite3
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATION = os.path.join(REPO_ROOT, "migrations", "0001-initial.sql")
TRIALS = 20
WRITERS_PER_TRIAL = 3
DB_PATH = "/tmp/sp-02-spike.db"


def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(open(MIGRATION, encoding="utf-8").read())
    conn.execute(
        "INSERT INTO scenario_runs (mode, scenario_file, team_size_config, started_at) "
        "VALUES ('batch','sp-02.json','{}',datetime('now'))"
    )
    conn.execute(
        "INSERT INTO agent_nodes (scenario_run_id, role_type, status, last_heartbeat_at) "
        "VALUES (1,'Medical','alive',datetime('now'))"
    )
    conn.commit()
    conn.close()


def make_contested_unit(trial_id):
    """Insert one fresh available unit plus one real agent_proposals row per
    writer (units.reserved_by_proposal_id is a real foreign key in our
    schema - using literal 1/2/3 without matching rows was the spike's
    first bug, caught by the FK constraint actually doing its job).
    Returns (unit_id, [proposal_id, proposal_id, proposal_id])."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.execute(
        "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, "
        "timestamp_reported, reporting_unit, status, received_at) "
        "VALUES (1,'spike-loc','moderate',datetime('now'),'spike-unit','created',datetime('now'))"
    )
    report_id = cur.lastrowid
    cur = conn.execute(
        "INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) "
        "VALUES (1,'Medical',1,'available')"
    )
    unit_id = cur.lastrowid
    proposal_ids = []
    for _ in range(WRITERS_PER_TRIAL):
        cur = conn.execute(
            "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, "
            "recommended_unit_id, reasoning, alternatives, model_identifier, "
            "model_version, generated_at) "
            "VALUES (?,1,80,?,'spike','[]','spike-model','0',datetime('now'))",
            (report_id, unit_id),
        )
        proposal_ids.append(cur.lastrowid)
    conn.commit()
    conn.close()
    return unit_id, proposal_ids


def writer(unit_id, proposal_id, result_path):
    """Run in a separate OS process. Attempts the real reserve() UPDATE,
    busy-waiting briefly on a locked database (SQLite's default busy
    behavior) rather than failing immediately, matching how a real
    caller would behave."""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            cur = conn.execute(
                "UPDATE units SET status='reserved', reserved_by_proposal_id=? "
                "WHERE id=? AND status='available'",
                (proposal_id, unit_id),
            )
            won = cur.rowcount == 1
    except sqlite3.OperationalError as exc:
        won = False
        with open(result_path, "a", encoding="utf-8") as f:
            f.write("proposal %d: OperationalError: %s\n" % (proposal_id, exc))
        conn.close()
        return
    conn.close()
    with open(result_path, "a", encoding="utf-8") as f:
        f.write("proposal %d: won=%s\n" % (proposal_id, won))


def run_trial(trial_id):
    unit_id, proposal_ids = make_contested_unit(trial_id)
    result_path = "/tmp/sp-02-trial-%d.txt" % trial_id
    if os.path.exists(result_path):
        os.remove(result_path)

    procs = []
    start = time.time()
    for proposal_id in proposal_ids:
        p = mp.Process(target=writer, args=(unit_id, proposal_id, result_path))
        procs.append(p)
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=10)
    elapsed = time.time() - start

    # Did any process hang past the join timeout?
    hung = any(p.is_alive() for p in procs)
    for p in procs:
        if p.is_alive():
            p.terminate()

    wins = 0
    if os.path.exists(result_path):
        for line in open(result_path, encoding="utf-8"):
            if "won=True" in line:
                wins += 1

    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT status, reserved_by_proposal_id FROM units WHERE id=?", (unit_id,)
    ).fetchone()
    conn.close()
    final_status, final_owner = row

    return {
        "trial": trial_id,
        "unit_id": unit_id,
        "elapsed_s": round(elapsed, 3),
        "hung": hung,
        "self_reported_wins": wins,
        "final_status": final_status,
        "final_owner": final_owner,
        "lost_write": final_status != "reserved",
        "double_win": wins > 1,
    }


def main():
    setup_db()
    results = [run_trial(t) for t in range(1, TRIALS + 1)]

    print("%-6s %-9s %-7s %-6s %-14s %-13s %-12s" % (
        "trial", "elapsed_s", "hung", "wins", "final_status", "final_owner", "problem"))
    problems = 0
    for r in results:
        problem = ""
        if r["double_win"]:
            problem = "DOUBLE-BOOKED"
        elif r["lost_write"]:
            problem = "LOST WRITE"
        elif r["hung"]:
            problem = "HUNG"
        if problem:
            problems += 1
        print("%-6d %-9s %-7s %-6d %-14s %-13s %-12s" % (
            r["trial"], r["elapsed_s"], r["hung"], r["self_reported_wins"],
            r["final_status"], r["final_owner"], problem))

    max_elapsed = max(r["elapsed_s"] for r in results)
    print("\n%d/%d trials clean. Max elapsed per trial: %.3fs." % (
        TRIALS - problems, TRIALS, max_elapsed))
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
