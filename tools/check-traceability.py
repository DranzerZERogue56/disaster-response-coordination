#!/usr/bin/env python3
"""Audit a requirements traceability matrix.

Usage:  python3 check-traceability.py [path-to-csv]
Default path: traceability-matrix.csv in the current directory.

Expected header:
  req_id,type,priority,requirement,source,design_element,test_id,measurement_method,status

Findings are printed grouped by kind. Exit status is 1 if any BLOCKER is found,
0 otherwise -- so you can run this in CI once your matrix is supposed to be clean.
"""

import csv
import sys
from collections import Counter

BLOCKERS = ("orphan requirement", "untested requirement", "unmeasurable NFR",
            "unrequested work", "duplicate id")


def audit(path):
    findings = []
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    ids = Counter(r["req_id"].strip() for r in rows if r["req_id"].strip())
    for req_id, count in sorted(ids.items()):
        if count > 1:
            findings.append(("duplicate id", req_id,
                             f"appears {count} times; identifiers must be unique and stable"))

    for line_no, row in enumerate(rows, start=2):
        req_id = row["req_id"].strip()
        kind = row["type"].strip().lower()
        design = row["design_element"].strip()
        test_id = row["test_id"].strip()
        method = row["measurement_method"].strip()

        if not req_id:
            label = design or f"row {line_no}"
            findings.append(("unrequested work", label,
                             "built or planned with no requirement behind it -- "
                             "cut it, or write the requirement and get it prioritized"))
            continue
        if not design:
            findings.append(("orphan requirement", req_id,
                             "no design element -- nothing in the system is responsible for it"))
        if not test_id:
            findings.append(("untested requirement", req_id,
                             "no test -- you cannot show it works, so it does not count"))
        if kind.startswith("non") and not method:
            findings.append(("unmeasurable NFR", req_id,
                             "no measurement method -- this is a wish, not a requirement"))

    return rows, findings


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "traceability-matrix.csv"
    try:
        rows, findings = audit(path)
    except FileNotFoundError:
        print(f"No such file: {path}", file=sys.stderr)
        return 2
    except KeyError as missing:
        print(f"Missing expected column: {missing}", file=sys.stderr)
        return 2

    print(f"{path}: {len(rows)} rows, {len(findings)} findings\n")
    for kind in BLOCKERS:
        hits = [f for f in findings if f[0] == kind]
        if not hits:
            continue
        print(f"{kind.upper()} ({len(hits)})")
        for _, label, why in hits:
            print(f"  - {label}: {why}")
        print()

    if not findings:
        print("Clean. Every requirement is designed, tested, and measurable.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
