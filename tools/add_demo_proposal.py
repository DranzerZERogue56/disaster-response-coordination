#!/usr/bin/env python3
"""add_demo_proposal.py - put one proposal in front of the dispatcher console so there is something to approve.

    python tools/add_demo_proposal.py [database-path]        default: $DB_PATH or data/dev.sqlite

Field reports over HTTP are refused while the sign-in is on (DEF-032), so a fresh install has an empty console. This
adds one deliberately vague report ("something happened, not sure how bad"); the rules model is unsure about it
(confidence 40), so it is NOT sent automatically: it waits for a person, and a unit is held for it. The hold lasts
4 minutes (FR-RES-02): approve it from http://127.0.0.1:8080/dispatcher before the clock runs out, or the unit is released
and the proposal times out. Run this again for another one. The app can be running while you do this.
"""
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = {
    "location": "Corner of 4th and Main",
    "severity_raw": "something happened, not sure how bad, no one is answering",
    "reporting_unit": "demo field report",
}


def add(db_path):
    path = Path(db_path)
    if not path.is_file():
        sys.exit(f"the database {db_path} does not exist; run ./script/setup first")
    saved = {name: os.environ.get(name) for name in ("DB_PATH", "AUTH_ENFORCED")}
    os.environ["DB_PATH"] = str(path.resolve())
    os.environ["AUTH_ENFORCED"] = "0"  # this process only: it files the report directly, it is not a web caller
    sys.path.insert(0, str(ROOT))
    try:
        from src.web_ui.app import create_app

        body = {**REPORT, "timestamp_reported": datetime.now(UTC).isoformat()}
        with create_app().test_client() as client:
            response = client.post("/reports", data=json.dumps(body), content_type="application/json")
    finally:
        for name, value in saved.items():  # leave the caller's environment as it was
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    result = response.get_json() or {}
    decision = result.get("decision") or {}
    if response.status_code != 201 or not decision.get("held_for_human"):
        sys.exit(f"the demo report was not held for a person (HTTP {response.status_code}): {json.dumps(result)[:200]}")
    return {"proposal_id": decision["proposal_id"], "unit_id": result["proposal"]["recommended_unit_id"]}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    db_path = argv[0] if argv else os.environ.get("DB_PATH", "data/dev.sqlite")
    result = add(db_path)
    print(f"Proposal {result['proposal_id']} is waiting for a person (unit {result['unit_id']} is held for it).")
    print("Open http://127.0.0.1:8080/dispatcher, sign in, and approve it within 4 minutes.")


if __name__ == "__main__":
    main()
