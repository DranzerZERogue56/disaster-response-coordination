#!/usr/bin/env python3
"""check_synthetic.py - NFR-SEC-03: no real incident data in the repository; every incident report is
synthetic.

    python tools/check_synthetic.py             # exit 1 if any report file breaks the rule
    python tools/check_synthetic.py --sample    # also print 10 reproducible reports for the manual spot-check

The rule (docs/requirements.md NFR-SEC-03, amended by CR-005): every incident report lives under
tests/data/ (generated test data) or seed/ (demo reports and scenarios), and every report is marked
"synthetic": true, either on the report itself or on the entry that wraps it. A "report" is any JSON
object that has a "severity_raw" field. The check fails on a report file anywhere else, or on a report
without the marker. It cannot prove a report is invented; the manual spot-check of 10 random reports for
real addresses or names, before each milestone submission, covers that.
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = ("tests/data", "seed")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache"}
SAMPLE_SEED = 20261105


def json_files(root):
    for path in sorted(Path(root).rglob("*.json")):
        if not SKIP_DIRS & set(path.relative_to(root).parts):
            yield path


def allowed_folder(rel):
    return any(rel == a or rel.startswith(a + "/") for a in ALLOWED)


def unmarked_reports(node, marked=False):
    """Yield every report object (has severity_raw) not covered by a synthetic:true marker."""
    if isinstance(node, dict):
        marked = marked or node.get("synthetic") is True
        if "severity_raw" in node and not marked:
            yield node
        for value in node.values():
            yield from unmarked_reports(value, marked)
    elif isinstance(node, list):
        for item in node:
            yield from unmarked_reports(item, marked)


def violations(root=ROOT):
    """Human-readable problems; an empty list means the rule holds."""
    problems = []
    for path in json_files(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if "severity_raw" not in text:
            continue  # not a report file
        if not allowed_folder(rel):
            problems.append(f"{rel}: a report file outside tests/data/ and seed/")
            continue
        try:
            data = json.loads(text)
        except ValueError:
            problems.append(f"{rel}: report file that is not valid JSON")
            continue
        missing = sum(1 for _ in unmarked_reports(data))
        if missing:
            problems.append(f"{rel}: {missing} report(s) without \"synthetic\": true")
    return problems


def _reports(node):
    if isinstance(node, dict):
        if "severity_raw" in node:
            yield node
        else:
            for value in node.values():
                yield from _reports(value)
    elif isinstance(node, list):
        for item in node:
            yield from _reports(item)


def sample(root=ROOT, n=10, seed=SAMPLE_SEED):
    """n reproducible reports as 'file: location | severity_raw', for the manual spot-check."""
    found = []
    for path in json_files(root):
        rel = path.relative_to(root).as_posix()
        if not allowed_folder(rel):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for report in _reports(data):
            found.append(f"{rel}: {str(report.get('location'))[:50]} | {str(report.get('severity_raw'))[:70]}")
    found = sorted(set(found))  # the same report text appears in several files; show each once
    return random.Random(seed).sample(found, min(n, len(found)))


def main():
    problems = violations()
    for p in problems:
        print("VIOLATION:", p)
    if "--sample" in sys.argv:
        print("\nManual spot-check (10 reproducible reports; look for real addresses or names):")
        for line in sample():
            print("  -", line)
    print("synthetic check:", "FAILED" if problems else "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
