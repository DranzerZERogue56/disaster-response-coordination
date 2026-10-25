#!/usr/bin/env python3
"""The CI smoke stage. Proves /healthz is honest in both directions:
green when the data store is reachable, and it actually fails — not
silently passes — when the data store is not (architecture.md's own
"each stage able to fail the build" requirement, Milestone 9).
"""
import importlib
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_with_real_db():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "smoke.sqlite")
        os.environ["DB_PATH"] = db_path
        conn = sqlite3.connect(db_path)
        with open("migrations/0001-initial.sql", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()

        import src.web_ui.app as app_module

        importlib.reload(app_module)
        resp = app_module.app.test_client().get("/healthz")
        if resp.status_code != 200:
            print("SMOKE FAIL: /healthz did not return 200 with a real data store")
            sys.exit(1)
        print("smoke: /healthz is healthy against a real data store")


def run_with_unavailable_db():
    # A directory, not a file: sqlite3 can't open it as a database — the
    # stand-in this skeleton uses for "the data store is down."
    os.environ["DB_PATH"] = tempfile.mkdtemp()

    import src.web_ui.app as app_module

    importlib.reload(app_module)
    resp = app_module.app.test_client().get("/healthz")
    if resp.status_code == 200:
        print("SMOKE FAIL: /healthz returned 200 with the data store unavailable")
        sys.exit(1)
    print(
        "smoke: /healthz correctly fails when the data store is unavailable (%s)"
        % resp.status_code
    )


if __name__ == "__main__":
    run_with_real_db()
    run_with_unavailable_db()
    print("smoke: all checks passed")
