#!/usr/bin/env python3
"""Verified-requirement coverage from a test traceability matrix.

Reads a CSV with the columns produced by the Week 11 test traceability matrix:

    req_id, req_priority, acceptance_criterion_id, test_case_id, level, status, defect_id

This is a *criterion-level* file: one row per acceptance criterion per test case. It is
a different, narrower artifact than the Week 4 requirements traceability matrix
(req_id, type, priority, requirement, source, design_element, test_id,
measurement_method, status), which has one row per requirement and is audited by that
week's checker. Keep the two files separate; this script cannot read the Week 4 one and
will tell you so instead of crashing.

It reports the only coverage number this course cares about: what fraction of your
requirements are *verified* -- meaning every one of their acceptance criteria has at
least one test case whose status is `pass`.

This is deliberately harsher than line coverage. Line coverage tells you which code a
test touched. This tells you which promises you have kept.

    python3 coverage_report.py                       # uses traceability-matrix.csv beside it
    python3 coverage_report.py path/to/matrix.csv

Stdlib only. Exit code 1 if any Must requirement is unverified, so you can wire it
into CI once you are ready to be held to it. Exit code 2 means the file was missing or
had the wrong columns -- that is a setup problem, not a coverage failure.
"""

import csv
import os
import sys
from collections import defaultdict

PASS = "pass"

# The columns this report actually reads. `level` and `defect_id` are part of the
# documented header but are not required to compute coverage.
REQUIRED_COLUMNS = ("req_id", "req_priority", "acceptance_criterion_id",
                    "test_case_id", "status")


class MatrixSchemaError(Exception):
    """Raised when the CSV is not a Week 11 test traceability matrix."""

    def __init__(self, missing, found):
        self.missing = list(missing)
        self.found = list(found)
        super().__init__(f"missing column(s): {', '.join(self.missing)}")


def cell(row, name):
    """Column value as a stripped string; tolerates short or ragged rows."""
    return (row.get(name) or "").strip()


def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        missing = [name for name in REQUIRED_COLUMNS if name not in header]
        if missing:
            raise MatrixSchemaError(missing, header)
        return [row for row in reader if cell(row, "req_id")]


def summarize(rows):
    criteria = defaultdict(list)          # (req_id, priority, ac_id) -> [status, ...]
    for row in rows:
        key = (cell(row, "req_id"), cell(row, "req_priority"), cell(row, "acceptance_criterion_id"))
        criteria[key].append((cell(row, "test_case_id"), cell(row, "status").lower()))

    untested, failing, not_run, verified_ac = [], [], [], set()
    for key, results in criteria.items():
        if not any(tc for tc, _ in results):
            untested.append(key)
        elif any(status == PASS for _, status in results):
            verified_ac.add(key)
        elif any(status == "fail" for _, status in results):
            failing.append(key)
        else:
            not_run.append(key)

    requirements = defaultdict(list)      # (req_id, priority) -> [ac_key, ...]
    for key in criteria:
        requirements[(key[0], key[1])].append(key)
    verified_req = {r for r, acs in requirements.items() if all(a in verified_ac for a in acs)}
    return requirements, verified_req, untested, failing, not_run


def pct(part, whole):
    return 0.0 if not whole else 100.0 * part / whole


def show(title, keys):
    if not keys:
        return
    print(f"\n{title}")
    for req_id, priority, ac_id in sorted(keys):
        print(f"  {req_id:<8} {priority:<7} {ac_id}")


def main(argv):
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traceability-matrix.csv")
    path = argv[1] if len(argv) > 1 else default
    try:
        rows = load(path)
    except FileNotFoundError:
        print(f"No such file: {path}", file=sys.stderr)
        return 2
    except MatrixSchemaError as error:
        print(f"{path}: missing column(s): {', '.join(error.missing)}", file=sys.stderr)
        print(f"  found:    {', '.join(error.found) or '(no header row)'}", file=sys.stderr)
        print(f"  expected: {', '.join(REQUIRED_COLUMNS)}", file=sys.stderr)
        print("  This report reads the Week 11 test traceability matrix (one row per "
              "acceptance criterion per test case), not the Week 4 requirements matrix. "
              "Keep them in separate files.", file=sys.stderr)
        return 2
    requirements, verified, untested, failing, not_run = summarize(rows)

    musts = {r for r in requirements if r[1].lower() == "must"}
    verified_musts = musts & verified
    print(f"Traceability matrix: {path}")
    print(f"Requirements:        {len(requirements)}")
    print(f"Verified:            {len(verified)}  ({pct(len(verified), len(requirements)):.0f}%)")
    print(f"Must requirements:   {len(musts)}")
    print(f"Verified Musts:      {len(verified_musts)}  ({pct(len(verified_musts), len(musts)):.0f}%)")

    show("NO TEST CASE AT ALL (write these first):", untested)
    show("TESTED AND FAILING (open a defect if you have not):", failing)
    show("TEST EXISTS BUT NEVER RUN (this is not coverage):", not_run)

    unverified_musts = sorted(musts - verified)
    if unverified_musts:
        print("\nUNVERIFIED MUST REQUIREMENTS -- exit criteria not met:")
        for req_id, priority in unverified_musts:
            print(f"  {req_id}")
        return 1
    print("\nAll Must requirements verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
