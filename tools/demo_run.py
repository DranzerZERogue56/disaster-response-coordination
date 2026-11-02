#!/usr/bin/env python3
"""demo_run.py - run the Milestone 10 demo (docs/demo/iteration-1-script.md)
against the real app and write what happened to a transcript.

    python tools/demo_run.py

It builds a fresh database with the seed, starts the app on port 8081 (so it
does not fight a copy you already have running on 8080), submits Reports A, B
and C, makes the dispatcher decision, runs the test suite, and stops only the
server it started. The transcript is the fallback record if a live run goes
wrong on camera; it is a real run, not a mock-up.
"""
import glob
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "demo-run.sqlite"
PORT = 8081
BASE = f"http://127.0.0.1:{PORT}"
OUT = ROOT / "docs" / "demo" / "iteration-1-run-transcript.md"

REPORTS = {
    "A": {
        "location": "4th & Main St",
        "severity_raw": "person fell, visible leg injury, conscious and talking",
        "timestamp_reported": "2026-11-01T12:00:00+00:00",
        "reporting_unit": "field-unit-7",
    },
    "B": {
        "location": "near the old warehouse on 2nd",
        "severity_raw": "something happened, not sure how bad, no one's answering",
        "timestamp_reported": "2026-11-01T12:05:00+00:00",
        "reporting_unit": "field-unit-7",
    },
    "C": {
        "location": "900 Elm Ave",
        "severity_raw": "man collapsed, chest pain, not breathing well",
        "timestamp_reported": "2026-11-01T12:10:00+00:00",
        "reporting_unit": "field-unit-3",
    },
}

log = []
started = time.time()


def stamp():
    seconds = int(time.time() - started)
    return f"{seconds // 60}:{seconds % 60:02d}"


def say(text):
    log.append(text)
    print(text)


def beat(title):
    say(f"\n## [{stamp()}] {title}\n")


def request(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def show(method, path, body=None):
    status, payload = request(method, path, body)
    say(f"`{method} {path}` -> HTTP {status}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```")
    return status, payload


def rows(sql):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    return out


def show_rows(title, sql):
    say(f"{title}\n\n```\n{sql}\n```\n```json\n{json.dumps(rows(sql), indent=2)}\n```")


def main():
    DB.parent.mkdir(exist_ok=True)
    if DB.exists():
        DB.unlink()
    env = {**os.environ, "DB_PATH": str(DB), "SWEEP_SECONDS": "5"}
    py = sys.executable

    say("# Iteration 1 demo: real run transcript")
    say(
        f"Run on {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} by `tools/demo_run.py` against the real app "
        "(fake model, seeded database). Elapsed times are real. This is the fallback record for "
        "`docs/demo/iteration-1-script.md`; the narrated screen recording is separate."
    )

    beat("Fresh database and seed")
    subprocess.run([py, "tools/migrate.py", str(DB)], cwd=ROOT, env=env, check=True, capture_output=True)
    conn = sqlite3.connect(DB)
    for path in sorted(glob.glob(str(ROOT / "seed" / "*.sql"))):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.close()
    show_rows("Seeded state: two Medical units, one stand-in dispatcher.", "SELECT id, unit_type, status FROM units")

    server = subprocess.Popen(
        [py, "-m", "flask", "--app", "src.web_ui.app", "run", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                if request("GET", "/healthz")[0] == 200:
                    break
            except OSError:
                time.sleep(0.2)
        else:
            raise SystemExit("the app did not start")

        beat("Start the app and check it is healthy")
        show("GET", "/healthz")

        beat("Report A (clear, happy path)")
        _, a = show("POST", "/reports", REPORTS["A"])

        beat("The proposal row in the database (model, confidence)")
        show_rows(
            "Proposal for Report A:",
            "SELECT id, confidence, recommended_unit_id, model_identifier, final_status, decided_by FROM agent_proposals WHERE id = 1",
        )

        beat("Confidence 75 or more and not Severe: auto-approved, unit assigned")
        show_rows("Unit 1 after auto-approval:", "SELECT id, status, reserved_by_proposal_id FROM units WHERE id = 1")

        beat("Notify Responder: a notification row, not yet acknowledged")
        show_rows("Notifications:", "SELECT id, assignment_id, unit_id, sent_at, acknowledged_at FROM notifications")

        beat("Report B (vague): low confidence, held for a person")
        _, b = show("POST", "/reports", REPORTS["B"])
        pid = b["proposal"]["proposal_id"]
        show_rows(
            "Proposal for Report B is still undecided:",
            f"SELECT id, confidence, final_status, decided_by FROM agent_proposals WHERE id = {pid}",
        )

        beat("The visible reservation clock")
        show("GET", "/units")

        beat("Say out loud: there is no login yet")
        say(
            "> There is no login yet. Anyone who can reach this address could press approve, and it always "
            "counts as the stand-in demo-dispatcher. Real login is planned before Milestone 12. This is a "
            "known, accepted gap for the demo."
        )

        beat("The stand-in dispatcher approves Report B's proposal")
        show("GET", "/proposals/pending")
        show("POST", f"/proposals/{pid}/decision", {"decision": "approve"})
        show_rows(
            "Decided by the dispatcher's id, not 'auto':",
            f"SELECT id, final_status, decided_by, decided_at FROM agent_proposals WHERE id = {pid}",
        )

        beat("Report C (failure path): both Medical units are taken")
        show("POST", "/reports", REPORTS["C"])
        show_rows(
            "Nothing was dispatched for C:",
            "SELECT id, status, reserved_by_proposal_id FROM units ORDER BY id",
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()

    beat("Run the test suite")
    tests = subprocess.run(
        [py, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    tail = "\n".join(tests.stdout.strip().splitlines()[-3:])
    say(f"```\n{tail}\n```")

    beat("What is not done")
    say(
        "Real dispatcher login (T-7.4) and the Scenario Reader (T-3.4). The classifier is a rules-based "
        "fake model; Ollama is the planned main model and is not wired in."
    )

    OUT.write_text("\n".join(log) + "\n", encoding="utf-8")
    DB.unlink(missing_ok=True)
    print(f"\nwrote {OUT}")
    return tests.returncode


if __name__ == "__main__":
    sys.exit(main())
