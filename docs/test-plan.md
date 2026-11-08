# Test Plan — Disaster Response Coordination

**Version:** 1.0  ·  **Author:** Ben (Dranzer Rogue), with the assistant drafting the facts  ·  **Date:** 2026-11-05  ·  **Baseline commit:** `9310c4a` (amended 2026-11-06; the first version named `9607340`; the exact commit of the final run is recorded in `docs/test-results.md`)

> **Status.** Written by the assistant from the repository and from Ben's decisions of 2026-11-05; read, confirmed and signed by Ben on 2026-11-05. The exit-criteria numbers in section 6 are Ben's. The AI policy for this milestone lets an assistant propose test material; Ben approves every assertion (he approved the test-to-criterion claims on 2026-11-05), and `docs/ai-usage.md` records what was proposed.

> **Amendment 1, 2026-11-06 (facts only; the exit criteria in section 6 are unchanged).** After this plan was signed the build grew: the plan to reach 90% verified-Must coverage built negotiation and tiebreaks, reconciliation, the Scenario Reader, node heartbeats and alerts, the model fallback chain, the modify action, a dispatcher console, a unit-status broadcast, the 24-hour purge job, a synthetic-data check and a clean-machine test (migrations 0005 to 0008, change requests CR-005 to CR-010). Sections 1 to 5 and 8 were rewritten so they describe the build that is actually tested. Nothing in section 6 was lowered; the only change to it was the earlier, dated rise from 60% to 90%. Ben to confirm this amendment (he signed the original on 2026-11-05).

---

## 1. Scope — what is under test

The build at the commit above and the requirement IDs in `docs/requirements.md` v1.4: all 30 functional requirements (FR-*) and all 14 non-functional requirements (NFR-*), 44 in total (31 Must, 6 Should... see the matrix for the exact split). Every one has a row in `docs/traceability.csv`, whether or not anything is built for it. The test plan covers what is **built**: intake and its offline queue, classify and propose (the fake model, behind a fallback chain), the unit registry and its 4-minute clock, the decide-proposal safety rule and the modify action, notification records, override assignment, negotiation (tiebreak, its log, the escalation queue, reconciliation of incident versions), the Scenario Reader, node heartbeats and alerts, the unit-status broadcast, the 24-hour purge job, the dispatcher console, the database rules (migrations 0002 to 0008), the synthetic-data check, the clean-machine test and the secrets scan. What is not built or not verifiable is shown in the matrix as a gap, not removed from it.

## 2. Out of scope — what is NOT under test, and why

| Not tested | Reason |
|---|---|
| Real language-model behaviour (Ollama, `phi4-mini`) | Not wired in; a rules-based fake stands in. Accuracy, latency and prompt behaviour of a real model are untested, and `docs/measurements.md` says so |
| Performance on the target hardware (RTX 3090/4090) | No such machine in the test environment. FR-INFER-02-AC1 and NFR-PERF-01-AC1 name that hardware, so they stay unverified rather than being marked passed on a laptop |
| The primary and smaller tiers of the fallback chain against real models | Those tiers are empty slots until Ollama is wired. The chain's order, retries and escalation are tested with simulated failing models; a real model failing to load is not |
| A real notification channel (FR-ALERT-01 beyond "a row is recorded") | The requirement names no channel (DEF-017); a database row is what is tested |
| Login, roles and CSRF (FR-AUTH-01); map output (FR-MAP-*); acknowledgment tracking (FR-ALERT-02); agent timeout (FR-AGENT-04) | Not built: Should, Could or Won't priority, or deferred. DEF-018 records the missing login at S2 |
| Browser and screen-reader behaviour of the dispatcher console (NFR-PORT-01, NFR-USE-01) | Only structure (native labelled controls, focus outline, contrast figures) is checked by tests, plus one manual keyboard-only pass; no automated accessibility checker, no second browser, no screen reader |
| Nodes as separate machines, and a real network between them | Heartbeat detection is measured with real separate processes on one machine sharing one SQLite file; network loss between machines is not tested |
| Load beyond one process (many concurrent users) | One SQLite database in one process is the design; the 8-thread reservation test is the concurrency evidence |
| The correctness of SQLite, Flask, Python, GitHub Actions | Not ours to verify |
| Security testing beyond input handling, secrets and the no-outbound-network checks | No login exists yet; a penetration test would be premature |

## 3. Test levels

| Level | What it covers here | How it runs | Roughly how many |
|---|---|---|---|
| Unit | Module logic against a temporary SQLite database: classify, registry, decide, notify, override, intake validation, measurement, plus property-based tests (below) | `./script/test` (whole suite) or `pytest tests/unit` | 328 (includes the property tests) |
| Integration | Real seams: the HTTP routes against a real database, real threads and the background sweeper, the migration runner and database triggers, the three test-data families through the real intake route | `pytest tests/integration` | 191 (includes a 33-second test that kills five real node processes) |
| Acceptance | One test per acceptance criterion of a built Must requirement, named after the criterion, driving the running app on a freshly seeded database | `pytest tests/acceptance` | 29 |
| Manual | Two criteria are manual by their own wording: a keyboard-only pass with the mouse unplugged (NFR-ACC-01) and a clean-machine run (NFR-MNT-01) | A written numbered script (`tests/manual/scripts/`), the result recorded with `tools/record_manual_result.py` and an evidence file; counted in the matrix only if on the record | 2 |

**One command for everything:** `./script/test`. It runs all three levels and the coverage gate, and is the same command CI runs.

**Test data (three families).** `tests/data/generate.py` writes `happy.json`, `boundary.json`, `hostile.json` from a fixed seed (20261105): byte-identical on every run, every entry marked `"synthetic": true`, no real personal data. Happy: 20 realistic reports. Boundary: 19 inputs on an edge (shortest and longest text, empty versus one character, earliest and latest time and offset, leap day). Hostile: 28 inputs a careless or malicious sender might send (SQL and markup, odd unicode, control characters, huge values, wrong types, non-object bodies). `./script/seed-test-data` regenerates and loads them.

**Property-based tests (Medium tier).** Four invariants, stated here in prose before they are code (Hypothesis, fixed seed, no wall-clock deadline):

1. **P1, the safety rule.** For any confidence from 0 to 100 and any severity, a proposal is dispatched without a person only when confidence is 75 or more and the severity is neither Severe nor Critical. Nothing else ever bypasses a person.
2. **P2, times keep their order.** For any two moments in time, written with any UTC offset, the stored text for the earlier moment sorts before the stored text for the later one, and every stored time is UTC. (This is what the offline queue's "oldest first" depends on.)
3. **P3, units are never double-booked.** After any sequence of reserve, approve, reject and clock-expiry steps, in any order, no unit is assigned unless its proposal is approved, no proposal holds more than one unit, and every reserved or assigned unit is held by exactly one proposal.
4. **P4, the model's answer is trusted only if it is exactly the right shape.** The validator accepts a model answer only if the severity and unit type are in their allowed sets, the confidence is a real whole number from 0 to 100 (not a boolean, a float, or text), and the reasoning is non-empty text.

## 4. Environment

| Item | Value |
|---|---|
| Runtime / language version | Python 3.11.8 locally; CI runs 3.11 and 3.12 (matrix) |
| Operating system(s) | Windows 11 locally; Ubuntu (GitHub Actions `ubuntu-latest`) in CI |
| Database / storage | SQLite 3.43.1, a fresh temporary file per test; migrations 0001 to 0008 applied by `tools/migrate.py` |
| Third-party services | None. The model is a rules-based fake; the network is not used (a test blocks outbound connections to prove it) |
| Test data set | `tests/data/*.json`, generated by `tests/data/generate.py` (seed 20261105) |
| Where it runs | Local `./script/test`, and the GitHub Actions workflow named **CI** on every push |
| Dependencies | `requirements.txt` pinned versions (pytest 9.1.1, hypothesis, pytest-cov) |

## 5. Entry criteria — we may begin testing when

- [x] The build under test is pushed and CI is green on the pipeline from Milestone 9 (green on `bbcae34` before this milestone's changes, and green on the build under test, `9310c4a`).
- [x] Every Must requirement that is built has at least one written test case (the matrix lists the ones that are not).
- [x] The test data set is checked in and loads without manual steps (`./script/seed-test-data`).
- [x] Acceptance criteria exist for the built Must requirements (CR-003 wrote six that were missing).
- [x] The requirements baseline is known and changes go through change requests (CR-001 to CR-010).

## 6. Exit criteria — verification is DONE when

Numbers, written before the matrix was first run (Ben's choices):

- [ ] **Verified-Must coverage is at least 90%**, measured by `tools/coverage_report.py` on `docs/traceability.csv`. *(Ben's number. It was 60% when this plan was signed on 2026-11-05; the first measurements were 32% and then 42%. After the failure-case criteria it stood at 52%, and Ben raised the bar to 90% on 2026-11-05 and chose to build the missing requirements rather than keep the lower target. The change is dated here so it is not mistaken for a quiet edit; it is an increase, not a softening. The work plan is `docs/superpowers/plans/2026-11-05-reach-90-percent-verified-must.md`.)*
- [ ] **0 open defects at severity S1 or S2** in `docs/defect-log.md`.
- [ ] Every open S3/S4 defect appears in the defect log with a documented workaround.
- [ ] **Every defect fixed this iteration has a named regression test that fails on the pre-fix commit** (checked by `tools/verify_regression.py`).
- [ ] The full suite runs from one documented command (`./script/test`) and passes in CI.
- [ ] **Line coverage of `src/` is at least 90%** (the gate in `./script/test`), reported beneath the verified-requirement number, not instead of it. *(Ben's number; the baseline measurement was 94%. 90% leaves room for ordinary change but fails if tests are deleted.)*

Results against these are in `docs/test-results.md`; any miss is annotated there, not edited out here.

## 7. Risks to the testing itself

| Risk | Trigger | Response |
|---|---|---|
| The fake model makes classification tests too easy | A real model changes severity or confidence for the same text | Tests state their expectation as the rule they check (a confidence threshold, a shape), not as the fake's exact number where possible; the measurement file says plainly it is the fake |
| Timing tests flake on a slow CI machine | The sweeper test and the 8-thread test fail intermittently | Clock logic uses an injected time, not the real clock; the real-thread tests wait up to 3 seconds with a generous deadline and are re-run before a failure is believed |
| Windows versus Linux differences | A test passes locally and fails in CI, or the reverse (line endings, paths) | CI runs on Linux every push; data comparisons normalise line endings |
| Property tests are random | A failure that cannot be reproduced | Fixed seed (`derandomize=True`), so a failing example is the same every run |
| Tests that preserve the code's bugs | A test is written from the implementation instead of the requirement | Acceptance tests are derived from the criterion text; the criteria were corrected or written first (CR-003) |
| The matrix drifts from the tests | A hand-edited CSV disagrees with what ran | The matrix is generated from the test results (`tools/build_traceability.py`), never edited by hand |

## 8. Schedule

What was planned, and what happened (kept honest; the plan changed on Thursday when the exit criterion was raised):

| When | What |
|---|---|
| Mon Nov 2 | Decisions: folder layout, matrix rename, Medium and Hard tiers, exit-criteria numbers |
| Tue to Wed | Test plan, traceability tooling, first honest coverage number (23% of requirements, 32% of Musts) |
| Thu Nov 5 | Test data, hostile-input testing, acceptance tests; defects DEF-009 to DEF-014 logged, then fixed. Evening: exit criterion raised from 60% to 90% verified-Must; the missing requirements built (Tasks 0 to 14 of the work plan), an independent review run, its findings logged as DEF-021 to DEF-028 and fixed |
| Fri Nov 6 | Push, CI fix, keyboard-only pass (Ben), results regenerated |
| Sat Nov 7 to Sun Nov 8 | Documents brought up to date, fresh-clone check, final commit; submit by 11:59 PM Central Sun Nov 8 |

## 9. Approval

I have read this plan and I am accountable for the exit criteria above.

Signed: Ben (Dranzer Rogue)  ·  Date: 2026-11-05
