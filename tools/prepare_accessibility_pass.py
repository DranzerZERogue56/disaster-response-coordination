#!/usr/bin/env python3
"""prepare_accessibility_pass.py - a known starting state for the manual keyboard-only pass (NFR-ACC-01).

    python tools/prepare_accessibility_pass.py [DB_PATH]       # default data/acc01.sqlite

Builds a fresh database (every migration, the demo seed, four spare units) and files four reports through the
real app code: one clear report, which is approved automatically and so shows up under Assignments (the target
for Override), and three vague ones, which the system holds for a dispatcher (the targets for Approve, Modify
and Reject). The holds are then released: a held proposal's unit is reserved for only 4 minutes, and a manual
pass takes longer than that. The three proposals stay waiting for a decision with no unit reserved, so they
cannot expire under the tester's hands; approving one simply reserves a unit at that moment. It prints the
command that starts the app on this database. Any existing file at DB_PATH is deleted first.
"""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CLEAR = "person fell, visible leg injury, conscious and talking"  # confidence 95, Serious: approved automatically
VAGUE = "something happened, not sure how bad, no one is answering"  # confidence 40: held for a dispatcher
SPARE_UNITS = 4


def _report(client, place, text):
    body = {"location": place, "severity_raw": text, "timestamp_reported": "2026-11-01T12:00:00+00:00", "reporting_unit": "field-unit-7"}
    response = client.post("/reports", data=json.dumps(body), content_type="application/json")
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()


def prepare(db_path):
    db_path = str(db_path)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    Path(db_path).unlink(missing_ok=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "migrate.py"), db_path], check=True, capture_output=True)  # noqa: S603
    conn = sqlite3.connect(db_path)
    conn.executescript((ROOT / "seed" / "iteration-1.sql").read_text(encoding="utf-8"))
    for _ in range(SPARE_UNITS):
        conn.execute("INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) VALUES (1, 'Medical', 1, 'available')")
    conn.commit()
    conn.close()

    previous = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = db_path
    try:
        from src.web_ui.app import create_app

        app = create_app()
        with app.test_client() as client:
            assigned = _report(client, "1st & Oak St", CLEAR)["proposal"]["proposal_id"]
            pending = [_report(client, place, VAGUE)["proposal"]["proposal_id"] for place in ("2nd & Elm St", "3rd & Pine St", "4th & Cedar St")]
    finally:
        if previous is None:
            os.environ.pop("DB_PATH", None)
        else:
            os.environ["DB_PATH"] = previous

    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE units SET status = 'available', reserved_by_proposal_id = NULL, reserved_at = NULL, "
        "released_expected_by = NULL WHERE status = 'reserved'"
    )
    conn.commit()
    conn.close()
    return {"db_path": db_path, "assigned_proposal": assigned, "pending_proposals": pending}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    summary = prepare(argv[0] if argv else "data/acc01.sqlite")
    print(f"Ready: {summary['db_path']}")
    print(f"  Waiting for a decision: proposals {summary['pending_proposals']}")
    print(f"  Assigned (for Override): proposal {summary['assigned_proposal']}")
    print("Start the app on it with:")
    print(f'  DB_PATH="{summary["db_path"]}" ./script/start')
    print("then open http://127.0.0.1:8080/dispatcher")
    return 0


if __name__ == "__main__":
    sys.exit(main())
