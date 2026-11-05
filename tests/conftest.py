"""Shared pytest setup for the whole suite.

Two markers connect tests to the specification (Milestone 11):

    @pytest.mark.covers("FR-INTAKE-02-AC1", ...)   the acceptance criteria this test verifies
    @pytest.mark.defect("DEF-003", ...)            the defect this test is the regression test for,
                                                   or that it currently exposes

After every run, the results are written to .pytest_criteria.json. tools/build_traceability.py
turns that file into docs/traceability.csv and tools/write_test_results.py into
docs/test-results.md, so the matrix is a measurement, not a hand-kept table.

A test that exposes a defect that is still open is marked xfail(strict=True): the suite stays
green, the matrix shows that criterion as "fail" with its defect id, and the moment the defect
is fixed the strict xfail turns red and forces the marker to be removed.
"""
import json
import time
from pathlib import Path

import pytest

RESULTS_FILE = Path(__file__).resolve().parent.parent / ".pytest_criteria.json"
_WORSE = {"pass": 0, "not_run": 1, "fail": 2}
_tests = {}
_counts = {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0}
_started = time.time()


def pytest_configure(config):
    config.addinivalue_line("markers", "covers(*criteria): acceptance criteria this test verifies")
    config.addinivalue_line("markers", "defect(*ids): defect this test is a regression test for, or exposes")


def _level(item):
    parts = Path(str(item.fspath)).parts
    for level in ("unit", "integration", "acceptance"):
        if level in parts:
            return level
    return "unit"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    failed_setup = report.when == "setup" and report.failed
    if report.when != "call" and not failed_setup and not (report.when == "setup" and report.skipped):
        return

    if report.skipped and hasattr(report, "wasxfail"):
        status, bucket = "fail", "xfailed"  # an open, known defect: the criterion is not met
    elif report.passed:
        status, bucket = "pass", "passed"
    elif report.skipped:
        status, bucket = "not_run", "skipped"
    else:
        status, bucket = "fail", "failed"
    _counts[bucket] += 1

    covers = [c for m in item.iter_markers("covers") for c in m.args]
    defects = [d for m in item.iter_markers("defect") for d in m.args]
    if not covers:
        return
    key = item.nodeid.split("[")[0]
    entry = _tests.setdefault(
        key, {"id": key, "level": _level(item), "criteria": covers, "defects": defects, "status": status}
    )
    if _WORSE[status] > _WORSE[entry["status"]]:
        entry["status"] = status


def pytest_sessionfinish(session, exitstatus):
    if session.config.getoption("collectonly", default=False):
        return
    RESULTS_FILE.write_text(
        json.dumps(
            {
                "counts": _counts,
                "seconds": round(time.time() - _started, 1),
                "tests": sorted(_tests.values(), key=lambda t: t["id"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
