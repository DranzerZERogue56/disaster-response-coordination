#!/usr/bin/env python3
"""measure_nfrs.py - repeatable measurements for the timing and loss targets in docs/requirements.md section 6.

    python tools/measure_nfrs.py release    # NFR-REL-02: a reserved unit returns to available within 4 min (real sweeper, real clock)
    python tools/measure_nfrs.py outage --reports 10 --minutes 2     # NFR-REL-03
    python tools/measure_nfrs.py outage --reports 100 --minutes 20   # NFR-REL-04
    python tools/measure_nfrs.py model      # NFR-PERF-01 with the real local model (Ollama), cold start separate from warm

Each run starts from a fresh database in a temp folder (migrations + seed), prints a JSON result, and writes it
to docs/evidence/m12-<name>.json. The wall clock is the real one: nothing is mocked or sped up.
"""
import argparse
import json
import math
import os
import platform
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from exe import path_of

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
EVIDENCE = ROOT / "docs" / "evidence"

SEEDS = [
    "person fell, visible leg injury, conscious and talking",
    "man collapsed, chest pain, not breathing well",
    "something happened, not sure how bad, no one is answering",
    "smoke coming from a second-floor window, people still inside",
    "child with a deep cut on the arm, bleeding but alert",
    "car crash, two people trapped, one unconscious",
    "family displaced by flooding needs shelter tonight",
    "man waving a weapon near the bus station",
    "elderly woman dizzy, short of breath, sitting on the curb",
    "kitchen fire put out, nobody hurt, smell of smoke",
]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[max(1, math.ceil(fraction * len(ordered))) - 1]


def environment():
    def sh(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False).stdout.strip()  # noqa: S603
        except Exception:  # noqa: BLE001
            return "unknown"

    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": " ".join(sh([path_of("powershell"), "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"]).split()),
        "gpu": " | ".join(x.strip() for x in sh([path_of("powershell"), "-NoProfile", "-Command", "(Get-CimInstance Win32_VideoController).Name"]).splitlines() if x.strip()),
        "ram_gb": round(int(sh([path_of("powershell"), "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"]) or 0) / 2**30, 1),
        "run": "fresh temp database, started from the terminal outside the editor, real wall clock",
    }


def fresh_db(extra_units=0):
    tmp = tempfile.mkdtemp(prefix="m12-")
    path = str(Path(tmp) / "measure.sqlite")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    for migration in sorted((ROOT / "migrations").glob("*.sql")):
        conn.executescript(migration.read_text(encoding="utf-8"))
    conn.executescript((ROOT / "seed" / "iteration-1.sql").read_text(encoding="utf-8"))
    for _ in range(extra_units):
        conn.execute("INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) VALUES (1, 'Medical', 1, 'available')")
    conn.commit()
    os.environ["DB_PATH"] = path
    return conn, path


def save(name, result):
    result["environment"] = environment()
    result["measured_at"] = datetime.now(UTC).isoformat()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / f"m12-{name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def release(args):
    """NFR-REL-02. Five units reserved by five undecided proposals; the app's own sweeper (5 s, as script/start) frees
    them when the 4-minute window ends. Also times five rejections, which free the unit at once."""
    from src.decide_proposal.service import decide_human, stub_dispatcher_id
    from src.unit_registry.service import reserve
    from src.web_ui.app import start_sweeper

    conn, _ = fresh_db(extra_units=8)
    start_sweeper(args.sweep)  # the interval script/start uses (5 s before the 2026-11-15 fix, 1 s after)

    def proposal(unit_id):
        rid = conn.execute(
            "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at, severity) "
            "VALUES (1, 'x', 'y', 't', 'u', 'classified', 't', 'Moderate')"
        ).lastrowid
        pid = conn.execute(
            "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, model_identifier, model_version, generated_at) "
            "VALUES (?, 1, 50, ?, 'r', '[]', 'fake', '1', 't')",
            (rid, unit_id),
        ).lastrowid
        conn.commit()
        return pid

    rejected_ms = []
    for unit_id in (1, 2, 3, 4, 5):  # rejection path
        pid = proposal(unit_id)
        reserve(conn, unit_id, pid)
        t = time.perf_counter()
        decide_human(conn, pid, "reject", stub_dispatcher_id(conn))
        rejected_ms.append(round((time.perf_counter() - t) * 1000, 2))
        assert conn.execute("SELECT status FROM units WHERE id = ?", (unit_id,)).fetchone()[0] == "available"

    units = (6, 7, 8, 9, 10)  # timeout path
    reserved = {}
    for unit_id in units:
        reserve(conn, unit_id, proposal(unit_id))
        reserved[unit_id] = datetime.fromisoformat(conn.execute("SELECT reserved_at FROM units WHERE id = ?", (unit_id,)).fetchone()[0]).timestamp()
    freed = {}
    deadline = time.time() + 330
    while len(freed) < len(units) and time.time() < deadline:
        for unit_id in units:
            if unit_id not in freed and conn.execute("SELECT status FROM units WHERE id = ?", (unit_id,)).fetchone()[0] == "available":
                freed[unit_id] = round(time.time() - reserved[unit_id], 2)
        time.sleep(0.25)
    seconds = [freed.get(u) for u in units]
    done = [s for s in seconds if s is not None]
    save(
        f"rel02-sweep{args.sweep:g}s",
        {
            "target": "NFR-REL-02: a reserved unit whose proposal is rejected or times out returns to available within 4 min (240 s)",
            "rejection_path_ms": rejected_ms,
            "timeout_path_seconds": seconds,
            "sweeper_interval_seconds": args.sweep,
            "n": len(done),
            "p50": percentile(done, 0.5) if done else None,
            "p95": percentile(done, 0.95) if done else None,
            "max": max(done) if done else None,
            "within_240s": all(s is not None and s <= 240 for s in seconds),
        },
    )


def outage(args):
    """NFR-REL-03 / REL-04. Go offline, submit N reports (they queue), wait, go online, count what was processed."""
    import json as _json

    from src.web_ui.app import create_app

    conn, _ = fresh_db()
    conn.close()
    app = create_app()
    client = app.test_client()
    assert client.post("/connectivity", json={"connected": False}).status_code == 200
    accepted = 0
    for i in range(args.reports):
        body = {"location": f"outage location {i}", "severity_raw": SEEDS[i % len(SEEDS)], "timestamp_reported": f"2026-11-15T12:{i % 60:02d}:00+00:00", "reporting_unit": "measure"}
        accepted += client.post("/reports", data=_json.dumps(body), content_type="application/json").status_code in (200, 201, 202)
    queued = client.get("/connectivity").get_json()["queued_reports"]
    print(f"submitted {args.reports}, accepted {accepted}, queued {queued}; waiting {args.minutes} min offline...", flush=True)
    time.sleep(args.minutes * 60)
    start = time.time()
    drained = client.post("/connectivity", json={"connected": True}).get_json()
    elapsed = round(time.time() - start, 2)
    check = sqlite3.connect(os.environ["DB_PATH"])
    processed = check.execute("SELECT COUNT(*) FROM incident_reports WHERE status != 'queued'").fetchone()[0]
    stuck = check.execute("SELECT COUNT(*) FROM incident_reports WHERE status = 'queued'").fetchone()[0]
    total = check.execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0]
    lost = args.reports - total
    save(
        f"outage-{args.reports}x{args.minutes}min",
        {
            "target": "NFR-REL-03: 2-minute outage, 10 reports, 0 lost, all processed" if args.reports == 10 else "NFR-REL-04: 20-minute outage, 100 reports, at most 2% lost",
            "reports_submitted": args.reports,
            "accepted_while_offline": accepted,
            "queued_at_end_of_outage": queued,
            "outage_minutes": args.minutes,
            "rows_in_database": total,
            "processed_after_reconnection": processed,
            "still_queued": stuck,
            "lost": lost,
            "lost_percent": round(100 * lost / args.reports, 2),
            "drain_seconds": elapsed,
            "drain_response_keys": sorted(drained) if isinstance(drained, dict) else None,
        },
    )


def model(args):
    """NFR-PERF-01 with the real local model. Cold start (model unloaded first) is reported on its own."""
    from src.classify_propose.measure import SEED_REPORTS, measure
    from src.classify_propose.ollama_client import DEFAULT_MODEL, OllamaModel

    subprocess.run([path_of("ollama"), "stop", DEFAULT_MODEL], capture_output=True, check=False)  # noqa: S603, S607
    time.sleep(2)
    result = measure(model=OllamaModel(timeout=60.0), texts=SEED_REPORTS[:20])
    seconds = result["seconds"]
    warm = seconds[1:]
    save(
        "perf01-real-model",
        {
            "target": "NFR-PERF-01: classification within 5 s, p95 over 20 seeded reports, on the target hardware (24 GB GPU, local model)",
            "model": result["model"],
            "reports": len(seconds),
            "cold_first_call_seconds": round(seconds[0], 3),
            "all_20": {"p50": round(percentile(seconds, 0.5), 3), "p95": round(percentile(seconds, 0.95), 3), "max": round(max(seconds), 3)},
            "warm_19": {"p50": round(percentile(warm, 0.5), 3), "p95": round(percentile(warm, 0.95), 3), "max": round(max(warm), 3)},
            "per_call_seconds": [round(s, 3) for s in seconds],
            "confidence_min_mean_max": [result["confidence_min"], round(result["confidence_mean"], 1), result["confidence_max"]],
            "human_review_share": result["human_review_share"],
            "verdict_note": "this laptop is not the target hardware; the row stays 'unverified on target' whatever the numbers",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("release")
    r.add_argument("--sweep", type=float, default=1.0, help="sweeper interval in seconds (script/start default)")
    r.set_defaults(fn=release)
    o = sub.add_parser("outage")
    o.add_argument("--reports", type=int, required=True)
    o.add_argument("--minutes", type=float, required=True)
    o.set_defaults(fn=outage)
    sub.add_parser("model").set_defaults(fn=model)
    args = parser.parse_args()
    args.fn(args)
