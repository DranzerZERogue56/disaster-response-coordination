# Test results

The record of the last full run, written by `python tools/write_test_results.py` (nothing here is typed by hand except the sections marked as commentary).

| Item | Value |
|---|---|
| Commit tested | `f05529b` (working tree had uncommitted changes to tracked files) |
| Date | 2026-11-16 05:12 UTC |
| Command | `./script/test` (equivalent: `python -m pytest --cov=src --cov-report=term-missing:skip-covered --cov-fail-under=90`) |
| Result | 684 passed |
| Duration | 354.78 s |
| Plan | `docs/test-plan.md` v1.0 |

## The four coverage numbers (`tools/coverage_report.py` on `docs/traceability.csv`)

| Number | Value |
|---|---|
| Total requirements | 44 |
| Verified requirements | 30 |
| **Verified-requirement coverage** | **68%** |
| Must requirements | 31 |
| Verified Must requirements | 29 |
| **Verified-Must coverage** | **94%** |

For comparison, and beneath the number that matters: line coverage of `src/` is **96.12%**. High line coverage with low verified-requirement coverage is the course's own warning: the code that exists is well exercised, but many promises in the specification have nothing built behind them yet.

A requirement is *verified* only if every one of its acceptance criteria has at least one passing test. A criterion that was never written, or that no test covers, counts against it.

## Exit criteria (docs/test-plan.md section 6), checked against this build

| Exit criterion | Result | Measured |
|---|---|---|
| Verified-Must coverage at least 90% | MET | 29 of 31 = 94% |
| 0 open defects at severity S1 or S2 | MET | open: none |
| Every open S3/S4 defect has a documented workaround | MET | all documented |
| Every fixed defect has a regression test that fails on the pre-fix commit | MET | Result: 32 of 32 fixed defects proven |
| The suite runs from one command (`./script/test`) and passes | MET | 684 passed; CI: the latest completed CI run on GitHub is on commit `5652de9` with result **success** |
| Line coverage of src/ at least 90% | MET | 96.12% |

### Misses, annotated (not edited away)

- None.

### Must requirements not yet verified (2 of 31)

| Requirement | Why |
|---|---|
| FR-INFER-02 | names the target hardware (RTX 3090/4090) and a real model; neither is available, so it stays unverified instead of being passed on the fake model |
| NFR-PERF-01 | names the target hardware and a real model; the fake-model measurement exists in docs/measurements.md but is not claimed as verification |

## Open defects at the time of this run

- DEF-017: "Notify" only records a row; there is no way to notify a responder from the software (S3/P3, Open)
- DEF-019: No length limit: a 100,000-character location is accepted and stored (S4/P4, Will not fix)
- DEF-020: A report timestamped in the year 2099 is accepted (S4/P3, Open)
- DEF-032: With the sign-in on, field reports, the scenario tool and node heartbeats over HTTP are refused: they have no account (S3/P3, Open)

## What this run does not show

- The classifier is a rules-based fake. Nothing here says a real language model will classify correctly or fast enough (`docs/measurements.md`).
- Several "fails before the fix" proofs for the older defects are collection errors because the fixed feature did not exist yet; for DEF-009 to DEF-012 the hostile-data cases give the assertion-level proof (see `docs/regression-proof.md`).
- CI on the final pushed commit is checked after pushing: the latest completed CI run on GitHub is on commit `5652de9` with result **success**.
