"""Load the happy test-data family into a fresh database, through the real intake route.

    python tests/data/load.py [database-path]      default: data/test.sqlite

It deletes the file if it exists, applies every migration, adds the demo seed and extra Medical
units (so twenty reports never run out of units), then submits the 20 happy reports and prints what
the system did with them. Use ./script/seed-test-data to regenerate the data first and then load it.
"""
import glob
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAPPY = Path(__file__).resolve().parent / "happy.json"


def main():
    db_path = (ROOT / (sys.argv[1] if len(sys.argv) > 1 else "data/test.sqlite")).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)

    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob(str(ROOT / "migrations" / "*.sql"))):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript((ROOT / "seed" / "iteration-1.sql").read_text(encoding="utf-8"))
    for _ in range(40):
        conn.execute(
            "INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) VALUES (1, 'Medical', 1, 'available')"
        )
    conn.commit()
    conn.close()

    os.environ["DB_PATH"] = str(db_path)
    sys.path.insert(0, str(ROOT))
    from src.web_ui.app import create_app

    app = create_app()
    entries = json.loads(HAPPY.read_text(encoding="utf-8"))
    statuses = {}
    with app.test_client() as client:
        for entry in entries:
            code = client.post("/reports", data=json.dumps(entry["payload"]), content_type="application/json").status_code
            statuses[code] = statuses.get(code, 0) + 1
    print(f"loaded {len(entries)} happy reports into {db_path}: HTTP status counts {statuses}")
    return 0 if statuses == {201: len(entries)} else 1


if __name__ == "__main__":
    sys.exit(main())
