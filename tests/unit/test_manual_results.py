"""Task 0: manual results (tests/manual/results.csv) reach the traceability matrix, honestly."""
import csv
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import build_traceability as trace
import record_manual_result as manual


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    results = tmp_path / "results.csv"
    (tmp_path / "evidence.md").write_text("what happened", encoding="utf-8")
    monkeypatch.setattr(trace, "MANUAL_RESULTS", results)
    monkeypatch.setattr(trace, "load_results", list)  # no automated tests in this scenario
    return tmp_path, results


def rows_for(criterion):
    rows, _ = trace.build_rows()
    return [r for r in rows if r[2] == criterion]


def test_a_manual_pass_with_evidence_appears_in_the_matrix(workspace):
    root, results = workspace
    manual.record("MANUAL-MNT-01", "NFR-MNT-01-AC1", "pass", "Ben", "evidence.md", results=results, root=root)
    (row,) = rows_for("NFR-MNT-01-AC1")
    assert (row[3], row[4], row[5]) == ("MANUAL-MNT-01", "acceptance", "pass")


def test_a_manual_row_without_an_evidence_file_is_refused(workspace):
    root, results = workspace
    with pytest.raises(FileNotFoundError):
        manual.record("MANUAL-X", "NFR-MNT-01-AC1", "pass", "Ben", "no-such-file.md", results=results, root=root)
    assert not results.exists()


def test_a_manual_fail_is_shown_as_fail_not_pass(workspace):
    root, results = workspace
    manual.record("MANUAL-ACC-01", "NFR-ACC-01-AC1", "fail", "Ben", "evidence.md", results=results, root=root)
    (row,) = rows_for("NFR-ACC-01-AC1")
    assert row[5] == "fail"


def test_one_manual_result_can_cover_several_criteria(workspace):
    root, results = workspace
    manual.record("MANUAL-BOTH", "NFR-MNT-01-AC1;NFR-ACC-01-AC1", "pass", "Ben", "evidence.md", results=results, root=root)
    assert rows_for("NFR-MNT-01-AC1")[0][3] == rows_for("NFR-ACC-01-AC1")[0][3] == "MANUAL-BOTH"


@pytest.mark.parametrize("bad", ["", "maybe", "PASS", "passed"])
def test_only_pass_or_fail_can_be_recorded(workspace, bad):
    root, results = workspace
    with pytest.raises(ValueError):
        manual.record("MANUAL-X", "NFR-MNT-01-AC1", bad, "Ben", "evidence.md", results=results, root=root)


def test_every_recorded_manual_result_in_the_repo_has_an_evidence_file():
    with (REPO / "tests" / "manual" / "results.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [r["test_id"] for r in rows if not (REPO / r["evidence"]).is_file()] == []


def test_the_exit_criterion_in_the_plan_is_ninety_percent():
    plan = (REPO / "docs" / "test-plan.md").read_text(encoding="utf-8")
    section = plan.split("## 6. Exit criteria", 1)[1].split("## 7.", 1)[0]
    assert "Verified-Must coverage is at least 90%" in section
    assert "at least 60%**" not in section  # the old number is mentioned only in the dated note
