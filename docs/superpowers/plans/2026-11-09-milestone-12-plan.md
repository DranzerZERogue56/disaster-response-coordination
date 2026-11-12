# Milestone 12 Plan: Integrated Release Candidate & Change Log (target: 150%)

**Due:** Sun Nov 15, 2026, 11:59 PM Central. **Submit:** push + annotated tag name + commit SHA in the Canvas dropbox + the status block in the submission comment.
**Source:** the Canvas assignment text (read 2026-11-09). This plan follows its rubric line for line.
**Companion:** `2026-11-09-milestone-12-questions.md` (every decision and input this plan needs from Ben; question numbers like Q41 are referenced below).
**What "150%" means:** 100/100 on the Normal rubric, plus the full +25% Medium tier, plus the full +25% Hard tier. The extra-credit tiers are "up to", graded on quality, so the plan is to do few things very well.

## 0. Ground rules (from the assignment's AI policy and the repo's rules)

1. **Ben decides, in his own words, with his name and date:** every change-request disposition and impact analysis; every claim in `docs/security-review.md`; the RC exit-criteria numbers; the scope-decision memo. The assistant may draft structure, run tools, build code and tests, and assemble documents from Ben's answers, but is never the source of those claims. The AI log (`docs/ai-usage.md`) records each substantive use.
2. **Every advisory ID is verified by Ben** at https://github.com/advisories or https://osv.dev/ before it goes in a document (the assistant may run the scanner and list candidates; it may not be the source).
3. **Exit criteria are written and committed before anything is evaluated** (the "Strong" example in the assignment shows a recorded failure and the day it was fixed; that is the target tone).
4. **Never soften a criterion or hide a failure.** A miss is written beside the number.
5. Backseat role: the assistant poses decisions as questions; Ben does the deciding.
6. No push without Ben's word each time. Canvas stays read-only.

## 1. Rubric map: how each line reaches full marks

| Pts | Rubric line (exact wording) | Evidence file(s) | Full-marks test ("a stranger could...") | Gap today | Owner | Day |
|---|---|---|---|---|---|---|
| 14 | Release candidate: annotated tag on a commit that clones clean, sets up, and passes tests | tag `v0.9.0-rc.1` (name: Q106), `tools/clean_machine_test.py` run on the tagged commit, `docs/rc-verification.md` (or inside CHANGELOG/exit criteria) | `git tag -n` shows an annotated tag with a message; `git rev-parse` gives the SHA; a fresh clone at the tag, following only the README, sets up and `./script/test` passes in CI and locally | No release tag exists (only `iteration-1`, `v0.1.0-skeleton`, `milestone-3`). README must be re-verified for clean-clone | Assistant builds and verifies; Ben approves the tag | Fri-Sat (last) |
| 6 | Written exit criteria, recorded before evaluation, with results | `docs/rc-exit-criteria.md` (written + committed first; results appended) | Each line is a number or a command a stranger can run; the commit that holds the criteria predates the commit that holds the results; misses are shown | None written for the RC | Ben chooses the numbers (Q9-Q18); assistant formats and runs the checks | Mon (write), Sat (evaluate) |
| 12 | Integration evidence: seam map plus a passing integration test per Tier 1 seam | new "Seam map" section in `docs/architecture.md`; `docs/integration-evidence.md` (table: seam, tier, test id, result); `tests/integration/` | Every seam that crosses a process, network or storage boundary on an acceptance path is listed with its Tier and at least one named, passing test | Many integration tests exist (191) but no seam map and no seam-to-test table | Assistant drafts map and finds gaps; Ben confirms tiers (Q19-Q28) | Tue |
| 12 | Performance measured against your own targets: method, sample, p50/p95, action | `docs/performance.md` | All 14 NFRs are covered (numeric ones measured with p50/p95 and sample size, pass/fail ones with evidence and verdict); environment named next to each number; one target re-measured after a fix with both numbers | `docs/measurements.md` has NFR-PERF-01 (fake model) and NFR-REL-01 (5 trials) only | Assistant builds harness and runs; Ben chooses environment and interprets (Q29-Q42) | Tue-Wed |
| 14 | Security pass: seven areas, evidence in every row, findings dispositioned | `docs/security-review.md` | Seven rows (secrets, input, authentication, authorization, transport, dependencies, logging), each with evidence a stranger can re-run; every finding fixed or accepted with a reason; dependency findings carry a verified advisory ID and a reachability judgment | File does not exist. Known: DEF-018 (no login, S2), no CSRF, plain HTTP on localhost | Ben writes and owns; assistant runs tools and fixes code only on Ben's instruction (Q43-Q62) | Wed-Thu |
| 10 | Third-party failure modes documented; degradation implemented for at least one | failure-mode table in `docs/architecture.md` section 9; tests; demo script | Table covers slow, down, rate-limited, changed-response for each external dependency, and one degradation path is both implemented and demonstrated | Section 9 documents Ollama as the only dependency, but Ollama is not wired in. The fallback chain exists (simulated failures) | Assistant drafts table and code; Ben decides Ollama scope (Q63-Q76) | Wed-Thu |
| 14 | Change requests: one file per request, three-line impact analysis, disposition | `docs/change-requests/CR-0NN-*.md` + a row each in the `CHANGELOG.md` change table | Each file has cost, blast radius, risk in both directions, a disposition, a decider and a date; at least one REJECT and one DEFER with a named destination | CR-001 to CR-010 exist, all approved, all raised by the build, none a REJECT or DEFER | Ben (Q77-Q96); assistant formats from his words | Mon-Tue |
| 6 | Scope cuts recorded with rationale and destination; nothing silently deleted | `docs/requirements.md` (Deferred + date + CR ref), `docs/backlog.md`, `CHANGELOG.md` | Every cut requirement is marked Deferred with date and CR reference, appears in `docs/backlog.md` with estimate and acceptance criteria intact, and is noted in the change log | `docs/backlog.md` missing; three M7 deferrals exist without CR references | Ben decides cuts (Q97-Q104); assistant moves text | Tue-Thu |
| 8 | CHANGELOG.md a reviewer can follow, traced to IDs, with known issues | `CHANGELOG.md` | Keep a Changelog sections for the candidate, entries traced to FR/NFR/DEF/CR ids, a Known issues list with severity and workaround | File holds only the spec-change table, and its intro still says "No change requests have been raised" (stale) | Assistant drafts from the logs; Ben reviews (Q105-Q116) | Fri |
| 4 | Defect log, traceability matrix and hours log current through Week 12 | `docs/defect-log.md`, `docs/traceability.csv`, `docs/hours-log.csv` | All three updated through Nov 15, matrix rebuilt after the final test run | Hours rows end 2026-11-07 | Ben logs hours daily; assistant updates log and matrix | daily + Sat |

## 2. Workstreams in detail

### WS1. Exit criteria first (6 pts) - Monday
1. Ben answers Q9-Q18 (which numbers, what thresholds). 2. Assistant writes `docs/rc-exit-criteria.md` as numbers and runnable commands, in the style of the assignment's "Strong" example (date written, date evaluated, PASS/FAIL beside each). 3. Commit it alone, with message `rc exit criteria written before evaluation`, **before** any measurement or review result exists. 4. Evaluate on Saturday and append results; failures stay visible.
Candidate lines (to be confirmed or replaced by Ben): all Must requirements with a passing acceptance test (currently 29 of 31, with 2 documented unverifiable); zero open S1/S2 (currently DEF-018 is an open S2: decide Q44); security pass complete with every finding dispositioned; every NFR measured with each miss carrying a recorded decision; a clean clone passes from the README; CI green on the tagged commit.

### WS2. Change control and scope (14 + 6 pts) - Mon-Tue
1. Ben lists the real incoming requests (Q77-Q80). Assistant offers a candidate list from the project's own history (see questions file) but does not decide.
2. Per request Ben gives: cost (hours), blast radius (what files/requirements/tests it touches), risk of doing it and risk of not doing it, disposition (ACCEPT / REJECT / DEFER-to-named-place), decider and date. Assistant formats the CR file from his words and adds the changelog row.
3. At least one REJECT and one DEFER with a destination (a backlog item id, a milestone, or "Version 2").
4. For each cut: mark the requirement **Deferred** in `docs/requirements.md` with date and CR reference; copy its text, estimate and acceptance criteria to `docs/backlog.md` (nothing deleted); note it in the changelog. Also bring the three Milestone-7 deferrals (lines ~94, ~308, ~358 of requirements.md) up to the same standard (date + CR ref + backlog entry).
5. Open question flagged: CR-005 to CR-010 were drafted by the assistant during Milestone 11 and say "Raised by Ben / Decided by Ben". Under this week's policy a CR disposition is Ben's. See Q85-Q87.

### WS3. Integration evidence (12 pts) - Tuesday
Seams on the acceptance paths, initial list (Ben confirms tiers, Q19-Q22): browser form to Flask routes; Flask to SQLite (migrations and triggers); intake HTTP to classify to registry to decide to notify (the money path); scenario CLI to HTTP; node processes to the shared SQLite file (real processes); classify service to model provider (in-process today, a network seam if Ollama is wired); file system (scenario files, evidence files, test data); CI runner to the repo (GitHub Actions). Deliverables: seam-map diagram (Mermaid, text-based) in `docs/architecture.md`; `docs/integration-evidence.md` mapping seam to test id to latest result; any missing Tier 1 test written. Existing evidence to reuse: `tests/integration/*` (real database, real routes, real threads, real killed processes).

### WS4. Performance (12 pts) - Tue-Wed
All 14 NFRs get a row. Plan by type:
- **Timing/rate targets measured with p50/p95 and a sample:** NFR-PERF-01 (classification p95 <= 5 s; fake model now, real model if Ollama is wired, Q29-Q33), NFR-REL-01 (detection <= 30 s, extend from 5 to 20 trials for a real tail), NFR-REL-02 (unit freed within 4 min; measure with the real sweeper), NFR-REL-03 (10 reports through a 2-minute outage, 0 lost), NFR-REL-04 (100 reports, <= 2% lost; note the 20-minute outage can be run shortened with a stated method or run in full on the side, Q36), NFR-MNT-01 (clean clone to running app under 5 min), NFR-USE-01 (45 s per decision; needs two observed sessions with three proposals each: Ben plus a second person, Q37).
- **Pass/fail NFRs with evidence and a verdict (no percentile applies):** NFR-SEC-01..04, NFR-PRIV-01, NFR-ACC-01/02: link to the existing test or manual evidence and say so plainly.
- Environment named beside every number (this laptop, OS, Python, "clean seeded run outside the editor, started fresh").
- **Re-measure after a fix:** at least one target measured, found wanting or improved, changed, and measured again with both numbers shown. We do not manufacture a miss: if everything passes first time, the honest route is to measure under a harsher, stated condition (Q40-Q42) and fix what that exposes.

### WS5. Security pass (14 pts) - Wed-Thu (Ben-owned)
Seven areas, one row each, evidence a stranger can re-run: (1) secrets (`script/secrets-check`, full-history scan, `.env` untracked, `.env.example`); (2) input handling (hostile test data family, DEF-009..012, JSON-body fixes); (3) authentication (DEF-018: no login); (4) authorization (role checks in decide/override; observer role refused; no per-record ownership); (5) transport (localhost HTTP only, no TLS: accept with reason or fix); (6) dependencies (pip-audit or OSV scan of `requirements.txt` plus the verified advisory ID and a reachability judgment for each hit); (7) logging (what is logged, that no personal data is, the append-only logs, the 24-hour purge). Assistant runs the tools and produces raw output; Ben reads it, decides fix versus accept, writes the reason, and verifies each advisory ID himself. Findings that Ben chooses to fix become defect-log entries first (log before fixing), then fixes with regression tests.

### WS6. Third-party failure modes + degradation (10 pts) - Wed-Thu
Table in architecture section 9: for each external dependency, four modes (slow, down, rate-limited, changed-response): detection, behaviour, user-visible state, test. Dependencies to list (Q63): Ollama (designed, not wired), the Python packages at runtime (Flask, Werkzeug), GitHub Actions/Pages (CI and dashboard), optionally the OSV/GitHub advisory services used by the scanner. Degradation **implemented and demonstrated** for at least one: the model fallback chain (smaller model, rules, manual workflow with 6 retries at 10 s) already exists and is tested with simulated failures. To make it a true third-party seam and to earn the Medium-tier contract/chaos items cheaply, the recommended option is a minimal Ollama client as the primary tier, tested against a local stub HTTP server (down, slow, 429, changed response, malformed JSON), with the real model optional (Q64-Q70). The demonstration is a scripted run that kills the stub and shows the dispatcher console degrading and escalating.

### WS7. CHANGELOG, known issues, release (8 + 14 pts) - Fri-Sat
Keep a Changelog layout: a corrected intro, the change table (every CR with a row), `[Unreleased]` and `[0.9.0-rc.1] - 2026-11-xx` sections with Added / Changed / Fixed / Deprecated / Removed / Security, each entry traced (FR-, NFR-, DEF-, CR- ids), then **Known issues in 0.9.0-rc.1** in the assignment's "Strong" form (id, severity, user-visible effect, workaround, planned version). Release mechanics: freeze; run full tests; regenerate matrix and results; clean-clone check at the commit; create the annotated tag with a message; push the tag; verify with `git tag -n`, `git rev-parse`, and a fresh `git clone --branch v0.9.0-rc.1`. Submit tag + SHA in Canvas.

### WS8. Records (4 pts) - daily
Ben logs hours the same day (planned vs actual per day). Defect log gets every new defect before its fix. Traceability matrix rebuilt after the last test run (`./script/test` then `python tools/build_traceability.py`). Update `docs/ai-usage.md` for every substantive assistant use.

## 3. Medium tier (+25%): selection

Recommended four, in value order. Two done well beat five thin; the fourth is the one to drop if time is short.
1. **Dependency scanning in CI.** `pip-audit` (or OSV) step in `.github/workflows/ci.yml` that fails on a High/Critical advisory in a reachable path and warns otherwise; documented policy for reachable vs not (Ben's reachability judgment feeds the security review).
2. **A written threat model (one page).** `docs/threat-model.md`: trust boundaries, what an attacker wants, the two most exposed paths. Ben-owned; the assistant can draw the data-flow diagram from the architecture.
3. **A chaos rep in the test suite.** Automated test(s) that stub the model provider (or kill a node process) and assert the degraded behaviour end to end through the real routes, so the fallback cannot silently rot. Cheap because the chain exists.
4. **Performance in CI.** A test that fails the build when a named target regresses (candidate: intake-to-proposal p95 on the seeded set with a deliberately loose budget, or the NFR-REL-02 release timing with an injected clock). Must be honest about what it guards (in-process with the fake model, not the target hardware).
Alternates if the Ollama client is built: a kill switch (config flag that disables the Ollama tier without a redeploy, tested and in the runbook) and a contract test against a captured Ollama response fixture (with 429, timeout and malformed cases).

## 4. Hard tier (+25%): Scope Decision Memo

`docs/scope-decision-memo.md`, 2-3 pages, addressed to the advisor, **written by Ben**. Five parts, each with the exact thing the assignment asks for (see Q133-Q150): (1) hardest refusal, the impact analysis, the disposition, and the actual sentence sent to the requester; (2) the yes he regrets: what it cost, what it displaced, the rule that would have changed it; (3) the strongest possible case against his own cut, then the answer; (4) what ships broken, severity, workaround, how a user finds out, and whether the demo shows the degraded path or hides it; (5) the Week 16 prediction from measured velocity, with the early-warning trigger. The assistant can: pull velocity numbers from `docs/hours-log.csv`, list candidate decisions from the project history, and read drafts for factual errors against the repo. It cannot supply the judgment.

## 5. Schedule (budget 15 h for Ben; assistant works in parallel)

| Day | Ben's work (hours) | Assistant's work |
|---|---|---|
| Mon Nov 9 | Answer Q1-Q18 and Q77-Q80 (about 1.5 h); decide exit criteria numbers; list real requests; Week 12 Quiz can wait | Write `rc-exit-criteria.md` from Ben's numbers and commit it first; draft CR files from Ben's words; seam inventory |
| Tue Nov 10 | CR dispositions in own words (1.5 h); confirm seam tiers; choose performance environment | Seam map + integration-evidence table; any missing Tier 1 test; performance harness; start first-pass measurements; Ollama decision applied |
| Wed Nov 11 | Read performance numbers, decide fix targets; start security pass reading scanner output (2.5 h) | Run pip-audit/OSV and tools; failure-mode table draft; Ollama stub client + tests (if chosen); fix-then-re-measure target |
| Thu Nov 12 | Finish security review; verify advisory IDs at osv.dev (2 h); backlog and deferral decisions | Apply Ben's security fixes with defect-log-first discipline; CI scanning step; chaos and perf-in-CI tests; threat-model diagram |
| Fri Nov 13 | Threat model text; start scope-decision memo (2.5 h); NFR-USE-01 observed sessions (needs a second person) | CHANGELOG draft, known issues, requirements deferrals, backlog; update defect log and hours; dry-run clean clone |
| Sat Nov 14 | Finish memo; review changelog and known issues; evaluate exit criteria with the assistant (2 h) | Final full test run; matrix + results; evaluate exit criteria and record results; fresh-clone verification; tag candidate |
| Sun Nov 15 | Approve tag; push; Canvas submit with tag + SHA + status block; Week 12 Quiz; Pen Testing 11 (1 h) | Tag, push on Ben's word, CI check, verification commands |

## 6. Risks and stop-loss

- **Time:** Ben's actual hours ran 33% over plan on M11 (20 against 15). If Wednesday ends with security and performance not drafted, drop Medium item 4 first, then the Ollama client (fall back to documenting Ollama as designed-not-integrated with the chain as the demonstrated degradation).
- **No natural miss for "re-measured after a fix":** do not fabricate one; use a harsher stated condition or an existing real gap (Q40-Q42).
- **Open S2 (DEF-018) against an RC exit criterion of zero open S2:** either fix (minimal login) or record a documented miss. Either is allowed; hiding it is not (Q44).
- **Policy risk:** security-review claims or CR dispositions drafted by the assistant would forfeit credit and break the AI policy. Keep the pen in Ben's hand for those.
- **Pen Testing 11 and the Week 12 Quiz** compete for the same Sunday: do both by Saturday if possible.
- **A tag cannot be moved after submission without a trace:** create the tag only when the clean-clone check passes; if a later fix is needed, create `-rc.2` and say so in the changelog.

## 7. Verification before submit (the assignment's own commands)

```
git tag -n                                  # the annotated tag and its message
git rev-parse v0.9.0-rc.1                   # the SHA to submit
git clone --branch v0.9.0-rc.1 <repo url> /tmp/rc-check   # then follow only README.md; ./script/test must pass
```
Plus: CI green on the tagged commit; `python tools/build_traceability.py` run after the final `./script/test`; `docs/hours-log.csv` current; every new file from the repository layout in the assignment present (`CHANGELOG.md`, `docs/performance.md`, `docs/security-review.md`, `docs/backlog.md`, `docs/change-requests/`, `docs/scope-decision-memo.md`, `.env.example` tracked and `.env` not tracked).
