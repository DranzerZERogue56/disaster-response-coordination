#!/usr/bin/env python3
"""write_test_results.py - run the whole verification once and write docs/test-results.md.

    python tools/write_test_results.py

It (1) runs the suite exactly as ./script/test does (all three levels plus the 90% coverage gate),
(2) rebuilds docs/traceability.csv from that run, (3) runs the course's coverage_report.py on it for the
four coverage numbers, (4) reads docs/regression-proof.md and docs/defect-log.md, and (5) checks every
exit criterion in docs/test-plan.md section 6 against what it measured. A criterion that is missed is
written down as MISSED with the measured number beside it. Nothing here edits a criterion to fit the
build; if you want a different criterion, change the plan and say why.

Run tools/verify_regression.py first if you changed any fix or regression test.
"""
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "test-results.md"
THRESHOLD_VERIFIED_MUST = 60
THRESHOLD_LINE_COVERAGE = 90

# Why a Must requirement is not yet verified: a short reason per requirement, for the matrix reader.
REASONS = {
    "FR-ALERT-01": "failure-case criterion (AC2) not yet written; AC1 passes",
    "FR-AUDIT-01": "failure-case criterion (AC2) not yet written; AC1 passes",
    "FR-INFER-01": "second criterion (AC2) not yet written; AC1 passes",
    "FR-INFER-02": "names the target hardware (RTX 3090/4090) and a real model; neither is available, so it stays unverified instead of being passed on the fake model",
    "FR-SIM-01": "the scenario replay is not built; AC1 (same confidence three times) passes but the pace criterion is unwritten",
    "FR-RES-03": "AC1 to AC3 need other agents to broadcast to; no agents exist (DEF-016). AC4 (the 4-minute release) passes",
    "FR-COORD-01": "negotiation and tiebreaks not built (Milestone 12)",
    "FR-COORD-02": "negotiation and reconciliation not built (Milestone 12)",
    "FR-COORD-03": "negotiation and tiebreaks not built (Milestone 12)",
    "FR-DEGRADE-01": "node heartbeats not built",
    "FR-DEGRADE-02": "fallback chain not built; needs a real model first",
    "NFR-PERF-01": "names the target hardware and a real model; the fake-model measurement exists in docs/measurements.md but is not claimed as verification",
    "NFR-PRIV-01": "the 24-hour purge job does not exist",
    "NFR-REL-01": "needs node heartbeats (not built)",
    "NFR-ACC-01": "needs a real dispatcher UI and a manual keyboard-only pass",
    "NFR-ACC-02": "needs a real dispatcher UI and a manual grayscale pass",
    "NFR-MNT-01": "the clean-machine test is the Week 13 deliverable",
    "NFR-SEC-03": "wants synthetic data under data/synthetic/ with a check script; the test data lives in tests/data/ (a path mismatch, not yet reconciled)",
}


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, **kw)


def git(*args):
    return run(["git", *args]).stdout.strip()


def main():
    started = datetime.now(UTC)
    # checked first: the run itself rewrites docs/traceability.csv, which is not "dirty" in this sense
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    suite = run(
        [sys.executable, "-m", "pytest", "--cov=src", "--cov-report=term-missing:skip-covered", "--cov-fail-under=90", "-q", "--no-header", "-p", "no:cacheprovider"]
    )
    out = suite.stdout
    summary = re.findall(r"^(\d+ (?:passed|failed)[^\n]*?) in ([\d.]+)s", out, re.M)  # pytest -q prints no === rule
    counts, seconds = (summary[-1] if summary else ("unknown", "0"))
    line_cov = re.search(r"Total coverage: ([\d.]+)%", out)
    line_cov = float(line_cov.group(1)) if line_cov else 0.0

    run([sys.executable, "tools/build_traceability.py"])
    cov = run([sys.executable, "tools/coverage_report.py", "docs/traceability.csv"]).stdout
    total_req = int(re.search(r"Requirements:\s+(\d+)", cov).group(1))
    verified = re.search(r"Verified:\s+(\d+)\s+\((\d+)%\)", cov)
    musts = int(re.search(r"Must requirements:\s+(\d+)", cov).group(1))
    verified_musts = re.search(r"Verified Musts:\s+(\d+)\s+\((\d+)%\)", cov)
    v_n, v_pct = int(verified.group(1)), int(verified.group(2))
    vm_n, vm_pct = int(verified_musts.group(1)), int(verified_musts.group(2))

    # which Musts are unverified (from the matrix itself)
    import csv

    rows = list(csv.DictReader((ROOT / "docs" / "traceability.csv").open(encoding="utf-8")))
    by = {}
    priority = {}
    for r in rows:
        priority[r["req_id"]] = r["req_priority"]
        by.setdefault(r["req_id"], {}).setdefault(r["acceptance_criterion_id"], []).append(r["status"])
    unverified_musts = sorted(
        rid for rid, crit in by.items() if priority[rid] == "Must" and not all("pass" in s and "fail" not in s for s in crit.values())
    )

    log = (ROOT / "docs" / "defect-log.md").read_text(encoding="utf-8")
    table = [
        [c.strip() for c in line.strip().strip("|").split("|")]
        for line in log.splitlines()
        if re.match(r"\| DEF-\d{3} \|", line)
    ]
    open_serious = [(r[0], r[3], r[1]) for r in table if r[6] == "Open" and r[3] in ("S1", "S2")]
    open_minor = [r[0] for r in table if r[6] == "Open" and r[3] in ("S3", "S4")]
    reports = dict(zip(re.findall(r"^### (DEF-\d{3}) ", log, re.M), re.split(r"^### DEF-\d{3} .*$", log, flags=re.M)[1:], strict=True))
    no_workaround = [d for d in open_minor if "workaround" not in reports.get(d, "").lower()]
    fixed = [r[0] for r in table if r[6] == "Fixed"]

    proof_file = ROOT / "docs" / "regression-proof.md"
    proof = proof_file.read_text(encoding="utf-8") if proof_file.exists() else ""
    proven = re.search(r"\*\*Result:\*\* (\d+) of (\d+) fixed defects proven", proof)
    proof_ok = bool(proven) and proven.group(1) == proven.group(2) and int(proven.group(2)) >= len(fixed)

    gh = run(["gh", "run", "list", "--limit", "1", "--json", "conclusion,headSha,status"]).stdout
    try:
        last = json.loads(gh)[0]
        ci = f"the latest completed CI run on GitHub is on commit `{last['headSha'][:7]}` with result **{last['conclusion'] or last['status']}** (the run for the commit that contains this file is checked after it is pushed)"
    except (ValueError, IndexError):
        ci = "not checked (the GitHub CLI was unavailable); check the CI run on the pushed commit"

    sha = git("rev-parse", "--short", "HEAD")
    passed_all = suite.returncode == 0

    def status(ok):
        return "MET" if ok else "**MISSED**"

    crit = [
        (f"Verified-Must coverage at least {THRESHOLD_VERIFIED_MUST}%", status(vm_pct >= THRESHOLD_VERIFIED_MUST), f"{vm_n} of {musts} = {vm_pct}%"),
        ("0 open defects at severity S1 or S2", status(not open_serious), "open: " + (", ".join(f"{d} ({s})" for d, s, _ in open_serious) or "none")),
        ("Every open S3/S4 defect has a documented workaround", status(not no_workaround), "all documented" if not no_workaround else "missing: " + ", ".join(no_workaround)),
        ("Every fixed defect has a regression test that fails on the pre-fix commit", status(proof_ok), proven.group(0).replace("**", "") if proven else "docs/regression-proof.md not found; run tools/verify_regression.py"),
        ("The suite runs from one command (`./script/test`) and passes", status(passed_all), f"{counts}; CI: {ci}"),
        (f"Line coverage of src/ at least {THRESHOLD_LINE_COVERAGE}%", status(line_cov >= THRESHOLD_LINE_COVERAGE), f"{line_cov:.2f}%"),
    ]

    lines = [
        "# Test results",
        "",
        "The record of the last full run, written by `python tools/write_test_results.py` (nothing here is typed by hand except the sections marked as commentary).",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Commit tested | `{sha}`{' (working tree had uncommitted changes to tracked files)' if dirty else ''} |",
        f"| Date | {started.strftime('%Y-%m-%d %H:%M UTC')} |",
        "| Command | `./script/test` (equivalent: `python -m pytest --cov=src --cov-report=term-missing:skip-covered --cov-fail-under=90`) |",
        f"| Result | {counts} |",
        f"| Duration | {seconds} s |",
        f"| Plan | `docs/test-plan.md` v1.0 |",
        "",
        "## The four coverage numbers (`tools/coverage_report.py` on `docs/traceability.csv`)",
        "",
        "| Number | Value |",
        "|---|---|",
        f"| Total requirements | {total_req} |",
        f"| Verified requirements | {v_n} |",
        f"| **Verified-requirement coverage** | **{v_pct}%** |",
        f"| Must requirements | {musts} |",
        f"| Verified Must requirements | {vm_n} |",
        f"| **Verified-Must coverage** | **{vm_pct}%** |",
        "",
        f"For comparison, and beneath the number that matters: line coverage of `src/` is **{line_cov:.2f}%**. High line coverage with low verified-requirement coverage is the course's own warning: the code that exists is well exercised, but many promises in the specification have nothing built behind them yet.",
        "",
        "A requirement is *verified* only if every one of its acceptance criteria has at least one passing test. A criterion that was never written, or that no test covers, counts against it.",
        "",
        "## Exit criteria (docs/test-plan.md section 6), checked against this build",
        "",
        "| Exit criterion | Result | Measured |",
        "|---|---|---|",
    ]
    for name, result, measured in crit:
        lines.append(f"| {name} | {result} | {measured} |")

    lines += ["", "### Misses, annotated (not edited away)", ""]
    if vm_pct < THRESHOLD_VERIFIED_MUST:
        lines += [
            f"- **Verified-Must coverage is {vm_pct}%, short of the {THRESHOLD_VERIFIED_MUST}% target.** The target was set before the matrix was first run. The gap is the unbuilt half of the specification (negotiation, the fallback chain, node heartbeats, the model, scenario replay, the dispatcher UI, the purge job) plus failure-case criteria not yet written; it is not an unrun test. The first run measured 32%; acceptance tests, hostile data and fixes raised it to {vm_pct}%. Reaching {THRESHOLD_VERIFIED_MUST}% means building those features in Milestones 12 to 14, not writing more tests for what exists.",
        ]
    for d, s, _ in open_serious:
        lines.append(f"- **{d} is open at {s}.** See `docs/defect-log.md` for the reason it is open and the workaround; it must be fixed before v1.0.")
    if not (vm_pct < THRESHOLD_VERIFIED_MUST or open_serious):
        lines.append("- None.")

    lines += ["", f"### Must requirements not yet verified ({len(unverified_musts)} of {musts})", "", "| Requirement | Why |", "|---|---|"]
    for rid in unverified_musts:
        lines.append(f"| {rid} | {REASONS.get(rid, 'see docs/traceability.csv')} |")

    lines += [
        "",
        "## Open defects at the time of this run",
        "",
        *[f"- {r[0]}: {r[1]} ({r[3]}/{r[4]}, {r[6]})" for r in table if r[6] != "Fixed"],
        "",
        "## What this run does not show",
        "",
        "- The classifier is a rules-based fake. Nothing here says a real language model will classify correctly or fast enough (`docs/measurements.md`).",
        "- Several \"fails before the fix\" proofs for the older defects are collection errors because the fixed feature did not exist yet; for DEF-009 to DEF-012 the hostile-data cases give the assertion-level proof (see `docs/regression-proof.md`).",
        "- CI on the final pushed commit is checked after pushing: " + ci + ".",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {counts}; verified-Must {vm_pct}%; line coverage {line_cov:.2f}%")
    return 0 if passed_all else 1


if __name__ == "__main__":
    sys.exit(main())
