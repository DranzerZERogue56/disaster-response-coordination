#!/usr/bin/env python3
"""build_traceability.py - build docs/traceability.csv, the criterion-level test
traceability matrix (Milestone 11), from two sources of truth:

  1. docs/requirements.md: every requirement, its priority, its acceptance criteria
  2. the last pytest run: which tests name which criterion, and how they ended

    python tools/build_traceability.py            # write docs/traceability.csv
    python tools/build_traceability.py --list     # print every criterion id, then stop

A test names the criterion it verifies with a marker:

    @pytest.mark.covers("FR-INTAKE-02-AC1")

and may name the defect it is a regression test for (or that it currently
exposes) with `@pytest.mark.defect("DEF-003")`. tests/conftest.py records the
results of every run in .pytest_criteria.json; run the suite first.

Criterion ids are <requirement id>-AC<n>, numbered in the order the criteria
appear under "Acceptance criteria" in requirements.md. A criterion that was
never written (a TODO placeholder) still gets a row, so it shows as a gap. A
criterion with no test gets one row with an empty test_case_id: a visible gap,
not an omission. Each NFR is one criterion (NFR-...-AC1): its "how it is
measured" cell.

Columns: req_id, req_priority, acceptance_criterion_id, test_case_id, level,
status (pass | fail | not_run | blank for a gap), defect_id.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "docs" / "requirements.md"
RESULTS = ROOT / ".pytest_criteria.json"
MANUAL_RESULTS = ROOT / "tests" / "manual" / "results.csv"
OUT = ROOT / "docs" / "traceability.csv"
COLUMNS = ["req_id", "req_priority", "acceptance_criterion_id", "test_case_id", "level", "status", "defect_id"]


def parse_requirements():
    """[(req_id, priority, [(criterion_id, text_or_None)])]; None means 'not written'."""
    text = REQUIREMENTS.read_text(encoding="utf-8").replace("\r\n", "\n")
    out = []
    for m in re.finditer(r"^### ((?:FR)-[A-Z]+-\d+) .*?\n(.*?)(?=^### |^## |\Z)", text, re.S | re.M):
        rid, body = m.group(1), m.group(2)
        pr = re.search(r"\*\*Priority:\*\*\s*(\w+)", body)
        priority = pr.group(1) if pr else "?"
        crit = re.search(r"\*\*Acceptance criteria:\*\*\n(.*?)(?=\n\*\*|\n\n|\Z)", body, re.S)
        items = []
        if crit:
            for line in crit.group(1).split("\n"):
                if line.startswith("- "):
                    items.append(None if "TODO" in line else line[2:].strip())
        if not items:
            items = [None]
        out.append((rid, priority, [(f"{rid}-AC{i}", t) for i, t in enumerate(items, 1)]))
    for m in re.finditer(r"^\| (NFR-[A-Z]+-\d+) \| (.*?) \| (\w+)[^|]* \| (.*?) \|\s*$", text, re.M):
        rid, priority = m.group(1), m.group(3)
        out.append((rid, priority, [(f"{rid}-AC1", m.group(4).strip() or None)]))
    return out


def load_results():
    if not RESULTS.exists():
        sys.exit("No .pytest_criteria.json: run the suite first (./script/test).")
    return json.loads(RESULTS.read_text(encoding="utf-8"))["tests"]


def load_manual():
    """Manual test results (tests/manual/results.csv), shaped like automated ones. A row names one or
    more criteria separated by a semicolon; its status is exactly what the tester recorded."""
    if not MANUAL_RESULTS.exists():
        return []
    with MANUAL_RESULTS.open(newline="", encoding="utf-8") as f:
        return [
            {
                "id": r["test_id"],
                "level": r["level"] or "acceptance",
                "criteria": [c.strip() for c in r["criteria"].split(";") if c.strip()],
                "defects": [],
                "status": r["status"],
            }
            for r in csv.DictReader(f)
        ]


def build_rows():
    tests = load_results() + load_manual()
    by_criterion = {}
    for t in tests:
        for c in t["criteria"]:
            by_criterion.setdefault(c, []).append(t)
    rows, known = [], set()
    for rid, priority, criteria in parse_requirements():
        for cid, _text in criteria:
            known.add(cid)
            covering = by_criterion.get(cid, [])
            if not covering:
                rows.append([rid, priority, cid, "", "", "", ""])
            for t in sorted(covering, key=lambda x: x["id"]):
                rows.append([rid, priority, cid, t["id"], t["level"], t["status"], ",".join(t["defects"])])
    unknown = sorted(set(by_criterion) - known)
    return rows, unknown


def main():
    if "--list" in sys.argv:
        for rid, priority, criteria in parse_requirements():
            for cid, text in criteria:
                print(f"{cid:22} {priority:7} {(text or '[not written]')[:110]}")
        return
    rows, unknown = build_rows()
    if unknown:
        sys.exit("Tests name criteria that do not exist: " + ", ".join(unknown))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    gaps = sum(1 for r in rows if not r[3])
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} rows, {gaps} gaps (criteria with no test)")


if __name__ == "__main__":
    main()
