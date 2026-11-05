"""Task 2: NFR-SEC-03, no real incident data: every report is synthetic and lives where it should."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import check_synthetic as cs


def write(root, rel, data):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


REPORT = {"location": "1 Example St", "severity_raw": "chest pain", "reporting_unit": "u", "timestamp_reported": "t"}


@pytest.mark.covers("NFR-SEC-03-AC1")
def test_every_committed_report_file_is_marked_synthetic_and_in_an_allowed_folder():
    assert cs.violations(REPO) == []


def test_a_marked_report_inside_an_allowed_folder_is_accepted(tmp_path):
    write(tmp_path, "tests/data/ok.json", [{"synthetic": True, "payload": REPORT}])
    write(tmp_path, "seed/one.json", {**REPORT, "synthetic": True})
    assert cs.violations(tmp_path) == []


def test_a_report_without_the_marker_is_flagged(tmp_path):
    write(tmp_path, "tests/data/bad.json", [{"synthetic": True, "payload": REPORT}, {"payload": REPORT}])
    (problem,) = cs.violations(tmp_path)
    assert "tests/data/bad.json" in problem and "1 report(s) without" in problem


def test_a_report_file_outside_the_allowed_folders_is_flagged(tmp_path):
    write(tmp_path, "docs/leak.json", {**REPORT, "synthetic": True})  # marked, but in the wrong place
    (problem,) = cs.violations(tmp_path)
    assert "docs/leak.json" in problem and "outside" in problem


def test_json_that_is_not_a_report_is_ignored(tmp_path):
    write(tmp_path, "docs/data/calendar.json", {"weeks": [1, 2, 3]})
    assert cs.violations(tmp_path) == []


def test_the_marker_must_be_literally_true(tmp_path):
    write(tmp_path, "seed/maybe.json", {**REPORT, "synthetic": "yes"})
    assert len(cs.violations(tmp_path)) == 1


def test_the_ten_report_sample_is_reproducible_and_has_ten_reports():
    first, second = cs.sample(REPO), cs.sample(REPO)
    assert first == second and len(first) == 10
    assert all(" | " in line and ": " in line for line in first)
