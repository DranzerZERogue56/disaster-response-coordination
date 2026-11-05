#!/usr/bin/env python3
"""verify_regression.py - prove that every fixed defect's named regression test fails on the
commit just before the fix and passes on the current build (Milestone 11: "a named regression
test that fails against the pre-fix commit").

    python tools/verify_regression.py            # runs everything, writes docs/regression-proof.md

For each defect it makes a throwaway git worktree at <fix commit>^ (the parent), copies the
CURRENT tests into it (the fix commit's tests did not exist before the fix), runs the named test
there, and expects it to fail (an assertion failure, or an error because the feature did not exist
yet). Then it runs the same test on the current tree and expects a pass. Nothing in your working
tree is touched; the worktree is removed afterwards. Exit status is 1 if any defect is not proven.
"""
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "regression-proof.md"

# defect id, fix commit, test node (file::name). The fix commit's parent is the "pre-fix" build.
DEFECTS = [
    ("DEF-001", "c2638bb", "tests/unit/test_classify_propose.py::test_classifying_twice_does_not_make_a_second_proposal"),
    ("DEF-002", "068c3ef", "tests/integration/test_clock_and_atomicity_http.py::test_sweeper_frees_an_expired_reservation_with_nobody_asking"),
    ("DEF-003", "b8c124e", "tests/unit/test_human_decision.py::test_a_held_proposal_whose_clock_runs_out_times_out_and_leaves_the_pending_list"),
    ("DEF-004", "068c3ef", "tests/unit/test_clock_and_atomicity.py::test_auto_approve_failing_midway_does_not_leave_an_assigned_unit"),
    ("DEF-005", "068c3ef", "tests/integration/test_clock_and_atomicity_http.py::test_unit_lost_twice_gets_its_own_error_code_and_dispatches_nothing"),
    ("DEF-006", "b8c124e", "tests/integration/test_timestamps_and_concurrency_http.py::test_offline_queue_orders_by_real_time_across_time_zones"),
    ("DEF-007", "4eaa83e", "tests/unit/test_override_assignment.py::test_the_override_log_and_its_follow_ups_cannot_be_edited"),
    ("DEF-008", "d51b9e0", "tests/unit/test_spec_checks.py::test_no_must_requirement_sentence_contains_a_placeholder"),
    ("DEF-009", "4f4a5cc", "tests/unit/test_intake_validation.py::test_a_body_that_is_not_a_json_object_is_refused_not_crashed"),
    ("DEF-010", "4f4a5cc", "tests/unit/test_intake_validation.py::test_a_list_or_object_where_text_belongs_is_invalid_not_a_crash"),
    ("DEF-011", "4f4a5cc", "tests/unit/test_intake_validation.py::test_whitespace_only_text_is_invalid"),
    ("DEF-012", "4f4a5cc", "tests/unit/test_intake_validation.py::test_a_number_or_boolean_is_not_accepted_as_text"),
    # the same four, at assertion level: the hostile-data cases the defects were found by
    ("DEF-009", "4f4a5cc", "tests/integration/test_data_families_http.py::test_hostile_input_never_crashes_the_server[json-list-instead-of-object]"),
    ("DEF-010", "4f4a5cc", "tests/integration/test_data_families_http.py::test_hostile_input_never_crashes_the_server[list-as-severity]"),
    ("DEF-011", "4f4a5cc", "tests/integration/test_data_families_http.py::test_hostile_input_the_specification_rejects_is_rejected[whitespace-only-location]"),
    ("DEF-012", "4f4a5cc", "tests/integration/test_data_families_http.py::test_hostile_input_the_specification_rejects_is_rejected[number-as-location]"),
    ("DEF-013", "9607340", "tests/integration/test_human_approval_second_path_http.py::test_a_lost_unit_is_replaced_by_an_alternative_when_the_dispatcher_approves"),
    ("DEF-014", "9607340", "tests/unit/test_proposal_input_data.py::test_the_proposal_records_the_input_data_and_the_confidence_when_it_is_generated"),
    ("DEF-015", "4a0afc2", "tests/unit/test_model_answer_validation.py::test_reasoning_must_be_non_empty_text"),
]


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def run_test(directory, node):
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", node, "-q", "--no-header", "-p", "no:cacheprovider", "-x"],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        return "pass", out
    if proc.returncode in (2, 4, 5) or "ImportError" in out or "ModuleNotFoundError" in out or "cannot import" in out:
        return "error (the feature did not exist yet)", out
    return "fail (assertion)", out


def main():
    rows, unproven = [], []
    head = git("rev-parse", "--short", "HEAD").stdout.strip()
    for defect_id, fix, node in DEFECTS:
        parent = git("rev-parse", "--short", f"{fix}^").stdout.strip()
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "pre-fix"
            added = git("worktree", "add", "--detach", str(tree), parent)
            if added.returncode != 0:
                rows.append((defect_id, fix, parent, node, "could not check out", "-"))
                unproven.append(defect_id)
                continue
            try:
                # the current tests (and config), on the old code
                shutil.copytree(ROOT / "tests", tree / "tests", dirs_exist_ok=True)
                shutil.copy(ROOT / "pytest.ini", tree / "pytest.ini")
                if "test_spec_checks" in node:
                    # the document checks need their helper and the defect log to import; the
                    # requirements text is NOT copied, because the old text is what is under test
                    (tree / "tools").mkdir(exist_ok=True)
                    shutil.copy(ROOT / "tools" / "build_traceability.py", tree / "tools" / "build_traceability.py")
                    shutil.copy(ROOT / "docs" / "defect-log.md", tree / "docs" / "defect-log.md")
                before, _ = run_test(tree, node)
            finally:
                git("worktree", "remove", "--force", str(tree))
        after, _ = run_test(ROOT, node)
        ok = before != "pass" and after == "pass"
        if not ok:
            unproven.append(defect_id)
        rows.append((defect_id, fix, parent, node, before, after))
        print(f"{defect_id}  before fix: {before:40} now: {after}")

    lines = [
        "# Regression proof",
        "",
        f"Generated by `python tools/verify_regression.py` on {date.today().isoformat()} at commit `{head}`.",
        "",
        "For each fixed defect: the named regression test, run against the commit just before the fix "
        "(with the current tests copied onto the old code), must **not pass**; run on the current build it must **pass**.",
        "",
        "| Defect | Fix commit | Pre-fix commit | Regression test | Before the fix | Now |",
        "|---|---|---|---|---|---|",
    ]
    for defect_id, fix, parent, node, before, after in rows:
        lines.append(f"| {defect_id} | `{fix}` | `{parent}` | `{node.split('::')[1]}` | {before} | {after} |")
    lines += ["", f"**Result:** {len(rows) - len(unproven)} of {len(rows)} fixed defects proven." + (f" Not proven: {', '.join(unproven)}." if unproven else ""), ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{len(rows) - len(unproven)} of {len(rows)} proven; wrote {OUT.relative_to(ROOT)}")
    return 1 if unproven else 0


if __name__ == "__main__":
    sys.exit(main())
