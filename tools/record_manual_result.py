#!/usr/bin/env python3
"""record_manual_result.py - record the result of a manual test (Milestone 11).

Two criteria are manual by their own wording: a keyboard-only pass with the mouse unplugged
(NFR-ACC-01) and a timed clean-machine run (NFR-MNT-01). A person (or a tool) runs them from a
written script and records the outcome here. tools/build_traceability.py reads the file and puts the
rows in docs/traceability.csv next to the automated tests, so a manual result counts the same way
only if it is on the record: who, when, pass or fail, and an evidence file that exists.

    python tools/record_manual_result.py --id MANUAL-ACC-01 --criteria NFR-ACC-01-AC1 \\
        --status pass --tester Ben --evidence tests/manual/evidence/acc-01-notes.md

Several criteria may be given separated by a semicolon. A fail is recorded as a fail: it shows in the
matrix as a failing criterion, never as a pass.
"""
import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "tests" / "manual" / "results.csv"
COLUMNS = ["test_id", "criteria", "level", "status", "date", "tester", "evidence"]


def record(test_id, criteria, status, tester, evidence, level="acceptance", when=None, results=RESULTS, root=ROOT):
    """Append one manual result. Refuses a missing evidence file and anything but pass or fail."""
    if status not in ("pass", "fail"):
        raise ValueError(f"status must be pass or fail, not {status!r}")
    if not (Path(root) / evidence).is_file():
        raise FileNotFoundError(f"evidence file not found: {evidence}")
    results = Path(results)
    new_file = not results.exists() or results.stat().st_size == 0
    results.parent.mkdir(parents=True, exist_ok=True)
    with results.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        if new_file:
            writer.writerow(COLUMNS)
        writer.writerow([test_id, criteria, level, status, (when or date.today()).isoformat(), tester, evidence])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--id", required=True, help="a test id such as MANUAL-ACC-01")
    parser.add_argument("--criteria", required=True, help="criterion id(s), separated by a semicolon")
    parser.add_argument("--status", required=True, choices=["pass", "fail"])
    parser.add_argument("--tester", required=True)
    parser.add_argument("--evidence", required=True, help="path (from the repo root) to a file that shows what happened")
    args = parser.parse_args()
    try:
        record(args.id, args.criteria, args.status, args.tester, args.evidence)
    except (FileNotFoundError, ValueError) as exc:
        sys.exit(str(exc))
    print(f"recorded {args.id}: {args.status}")


if __name__ == "__main__":
    main()
