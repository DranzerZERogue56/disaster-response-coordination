#!/usr/bin/env python3
"""
PLACEHOLDER — replace this with the real hours_report.py from Canvas
course materials (see HW-Files/README.md and HW-Files/currentHW.md step 0).

This is a stand-in so `docs/hours-log.csv` has something to run against
in the meantime. It sums actual_hours from docs/hours-log.csv and prints
a total; it does not necessarily match whatever the real course script
checks for (weekly targets, milestone breakdowns, etc.).
"""
import csv
import sys
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "docs" / "hours-log.csv"


def main() -> int:
    if not LOG_PATH.exists():
        print(f"No hours log found at {LOG_PATH}", file=sys.stderr)
        return 1

    total = 0.0
    rows = 0
    with LOG_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            if "SAMPLE" in row.get("task", ""):
                continue
            try:
                total += float(row["actual_hours"])
                rows += 1
            except (KeyError, ValueError):
                continue

    print(f"Rows counted: {rows}")
    print(f"Total actual_hours: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
