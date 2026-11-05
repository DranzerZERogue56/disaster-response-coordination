#!/usr/bin/env python3
"""purge.py - run the retention purge (NFR-PRIV-01) against the project database.

    python tools/purge.py                          # delete incident data older than 24 hours
    python tools/purge.py --retention-hours 6      # a shorter window
    python tools/purge.py --now 2026-11-07T12:00:00+00:00   # pretend it is then (for tests and demos)

Uses DB_PATH like the app does (default data/dev.sqlite). Prints what was purged and reset as JSON. Meant to
run about once an hour (docs/architecture.md, Purge Job; the exact schedule is open question OQ-3). It is
an internal job: nothing in the web app can call it. Exit status 1, with the reason on stderr, if the purge
failed; a failed purge changes nothing.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import connect  # noqa: E402
from src.purge.job import RETENTION_HOURS, PurgeFailed, purge  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retention-hours", type=int, default=RETENTION_HOURS)
    parser.add_argument("--now", help="ISO 8601 time to treat as now (test-only)")
    args = parser.parse_args(argv)
    conn = connect()
    try:
        result = purge(conn, now=datetime.fromisoformat(args.now) if args.now else None, retention_hours=args.retention_hours)
    except PurgeFailed as exc:
        print(f"PURGE_FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
