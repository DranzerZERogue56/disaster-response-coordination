# Design Review Checklist — Disaster Response Coordination

Run 2026-10-18, Week 8 (the halfway checkpoint). Self-review plus an AI pass — no second human reviewer was available this week (see DR-007/ASM-05 on exactly that kind of dependency). Findings are logged in `docs/review/review-defect-log.csv`; this checklist cites them as evidence, not as a replacement for walking the real artifacts.

## Area 1 — Requirements complete and traceable

- [x] Every functional requirement has a unique id, an actor, an action, an object, and a condition. — `docs/requirements.md` §5, all FR entries follow the identifier/actor/action/object/condition shape established in Milestone 3.
- [x] Every functional requirement has acceptance criteria a stranger could execute without asking you a question. — Given/When/Then criteria present on every Must/Should FR. Re-ran `tools/check_requirements.py` fresh this week: 0 errors, 1 warning (**DR-011**, FR-RES-02 reads as a compound sentence; its 3 acceptance criteria already decompose it into separately testable cases, logged and accepted rather than split).
- [x] Every requirement carries a MoSCoW priority, and the Must set is written down as a list. — `docs/requirements.md` §5/§6; Must set traced in full in `docs/traceability.csv`.
- [x] Every non-functional requirement states a metric, a threshold, a condition, and a measurement method. — `docs/requirements.md` §6, 14 NFRs across 7 categories (Milestone 4).
- [x] The traceability matrix maps each Must requirement to at least one specification section. — **Fixed this week, DR-001**: `docs/traceability.csv`'s `design_element` column now points at real `architecture.md` §10 components/interfaces for all 44 rows, not the Milestone-4-era `TBD` placeholder.
- [x] The traceability matrix maps each Must requirement to at least one planned test. — **Fixed this week, DR-001**: `test_id` column now names the real `docs/wbs.csv` task(s) whose done-when is that requirement's de facto test, including which are deferred.
- [x] No requirement contains the words *user-friendly*, *fast*, *robust*, *intuitive*, *scalable*, or *etc.* without a number attached. — `tools/spec-check.py`'s vague-word list (a superset of this) ran clean against `architecture.md` in Milestone 6; a manual grep of `requirements.md` against this exact list turns up nothing unattached to a number.
- [x] The out-of-scope list exists and names at least three things you are deliberately not building. — `docs/requirements.md` §7, plus `architecture.md` §1's explicit out-of-scope list (FR-COORD-04, FR-MAP-02, NFR-PORT-01) and this week's three new Won't items (FR-INTAKE-03, FR-INFER-03, FR-MAP-01, Milestone 7 §7).

## Area 2 — Interfaces fully specified

- [x] Every external interface is listed in one place. — `docs/architecture.md` §5, 11 interfaces (10 original + the Purge Job caught and added during Milestone 6's own traceability pass).
- [x] Each interface names its inputs with types, its outputs with types, and its error responses. — All 11 interfaces follow the 8-fact contract (Purpose/Auth/Request/Success/Errors/Idempotency/Side effects/Limits).
- [x] Status codes or exit codes are enumerated, including the failure cases, not just the happy path. — `architecture.md` §5's status-code policy table (9 codes, including 409/422/503 failure cases).
- [x] Authentication and authorization are stated per interface, not assumed globally. — Each interface's Auth field states its own requirement (e.g. Decide Proposal's interactive path requires a dispatcher-role session; Submit Incident Report is explicitly unauthenticated).
- [x] Every third-party service you call is named with the specific operation you call, and what you do when it is unavailable. — `architecture.md` §9, the Ollama/`llama3.2:3b` dependency spec, with FR-DEGRADE-02's fallback chain named explicitly.
- [x] Rate limits, quotas, timeouts, and retry behavior are stated as numbers. — `architecture.md` §8's timeout/retry table (60s LLM timeout, 5s Web UI timeout with 3 retries, etc.).
- [x] Nothing in the interface section says "handle errors appropriately." — Confirmed by `tools/spec-check.py`'s vague-word check, Milestone 6, still true (no edits to §5 since).

## Area 3 — Data model sound

- [x] Every entity has a primary key and named attributes with types. — `docs/architecture.md` §6, all 8 entities, plus `migrations/0001-initial.sql` as the executable version of the same claim.
- [x] Every relationship states its cardinality and what happens on delete. — §6's Relationships rows per entity; CHECK constraints in the migration enforce several of them at the database layer, not just in prose.
- [x] Units are explicit for every quantity, duration, money, and measurement field. — Hours in plan.md are always `h`; confidence is always the stated 0–100 scale; no unlabeled numeric field found in a walkthrough of §6.
- [x] Time fields state a time zone policy and a storage format. — §6: "every timestamp column is ISO 8601 UTC, generated at write time. Local time is computed exactly once, in the Dispatcher Web UI's rendering layer."
- [x] Personal data is identified as such, with a retention and deletion answer. — NFR-PRIV-01 (24h purge) plus §6's Purge Job interface; `dispatcher_accounts.is_fictional_test_account` makes the "no real person's data" claim checkable, not just asserted.
- [x] There is a migration story: how the schema changes after data exists. — §6 Migrations subsection: forward-only, `schema_migrations` table, `tools/migrate.py` — and it was actually run against a throwaway database in Milestone 6, not just described.
- [x] At least one worked example row exists for each core entity. — `spikes/sp-02-sqlite-write-contention.py` inserts and reads real rows in all 8 tables as part of the spike; not a separate "example data" artifact, but real exercised rows exist in the repo's history.

## Area 4 — Risks owned

- [x] The register itself is current, not a stale duplicate. — **Found this week, DR-010**: `RISKS.md` (the Milestone-1-era draft) was still linked from `README.md` as if current, explicitly self-labeled "to be formalized at Milestone 7" with no note that it had been. Marked superseded, pointing at `docs/risk-register.md`.
- [x] Every risk in the register has a likelihood, an impact, a trigger, an owner, and a response. — All 10 risks fully scored, including R-10 (new this week, DR-005), scored L4/I2 by the author 2026-10-18.
- [x] The response is an action, not an attitude. — Every risk's response names a concrete task or a specific fallback (e.g. R-01: "timebox a 2-hour spike... before committing further hours").
- [partial] Every technology you have never used before appears as a risk. — Mesa (R-01), GPU/local model (R-04), llama3.2:3b calibration (R-03) covered. **Flask/the Web UI was missing — DR-005, fixed this week as R-10.**
- [x] Every free tier, trial, credit, or borrowed access appears as a risk with an expiry date. — N/A, defensibly: every dependency in this project is either free-forever open source (Ollama, Mesa, SQLite, Python) or local hardware with no trial/credit structure (CON-03 rules out paid APIs by design). Stated here rather than silently skipped.
- [x] Every dependency on another human being appears as a risk. — ASM-05 (dispatcher reachability) lives in `requirements.md`'s Assumptions table, the correct home per the course's own constraint/assumption/dependency distinction (see DR-008 — checked, not a gap) — and it's now resolved (DR-007), not open.
- [x] At least one risk has already had its trigger checked this week, with the result written down. — R-05's trigger (calibrated plan exceeds plannable capacity) fired and was checked twice: 2026-10-07 (mitigated to a 14.1h residual) and 2026-10-10 (closed completely, 0.8h to spare) — both recorded in `docs/risk-register.md` and `docs/plan.md` §7.

## Area 5 — Definition of done written

- [x] The definition of done is a single list that applies to every requirement. — `docs/definition-of-done.md`, 9 items, retitled this week (DR-003) from the leftover template header.
- [x] It names the test evidence required before a requirement counts as done. — Item 2: "every acceptance criterion... checked by running it."
- [x] It names the documentation required before a requirement counts as done. — Item 7 (AI usage logged) plus the reconciled CHANGELOG.md note (DR-004) clarifying what's covered now versus Week 13.
- [x] It states what "merged" means: branch, review, checks passing. — Explicitly cut, with a dated reason (solo dev, no CI until Milestone 9) rather than a silent gap — the "What I cut" section names this directly.
- [x] It is achievable in the hours you have — check one Must requirement against it end to end. — Checked against FR-RES-03 (unit reservation): traces to a requirement (yes), has a real spike proving the behavior under concurrency (SP-02), is covered by a planned test (T-11.3, deferred per Milestone 7 but with real evidence already in hand per SP-02), and the hours log is current. Passes all nine items.

## Area 6 — Plan within budget

- [x] The work breakdown covers every Must requirement; no Must requirement lacks a task. — `docs/traceability.csv`'s rebuilt `test_id` column (DR-001) makes this checkable directly: every Must row names a real `docs/wbs.csv` task.
- [x] Every task has an estimate produced by a stated method, not a round number guessed at. — Three-point (O/M/P) PERT estimates on all 39 tasks, `docs/wbs.csv`.
- [partial] The total estimate for the Must set fits inside the hours remaining, with buffer left over. — **Fits, but the margin is thin (DR-009)**: 111.8h active against 112.5h plannable, 0.8h to spare. Technically passes; practically close enough that R-05/R-07 stay live risks, not closed ones.
- [x] The schedule names which week each work package finishes. — `docs/plan.md` §5, all 12 work packages assigned to specific weeks with a gate condition each.
- [x] The hours log is current through this week and matches the calendar. — `docs/hours-log.csv` current through 2026-10-10 (Milestone 7); this week's design-review hours still need logging after this document is committed.
- [x] Buffer is a named, quantified line in the plan, not the hope of working faster later. — 25% / 37.5h, `docs/plan.md` §2, confirmed intact (not eaten into) as of the Milestone 7 close-out.

---

## Entry criteria

1. **All six artifacts in the repository and pushed.** `requirements.md`, `architecture.md`, `plan.md`, `risk-register.md`, `definition-of-done.md`, `traceability.csv` — all present, all current as of this review.
2. **The author ran this checklist over their own package first.** This document — self-review plus one AI pass, both logged in `docs/ai-usage.md`.
3. **No load-bearing section says TBD.** Was false at the start of this review (DR-001, DR-002) — fixed before this checklist was marked complete.
4. **The reviewer's brief names the time box and what kind of finding is wanted.** This review: no formal time box set in advance (a real gap — no second human reviewer was scheduled this week, see DR-007/ASM-05), self-conducted in one sitting against all six artifacts plus an AI pass for cross-checking.

## Exit criteria

1. **Every Critical and Major defect has a written disposition.** DR-001 (Critical, fixed) through DR-011 (Minor, accepted) — all 11 dispositioned in `docs/review/review-defect-log.csv`.
2. **Every rejected finding has a written reason.** DR-008 — rejected with reasoning (correct location, already resolved).
3. **Rework on Majors is verified, and the verification is recorded.** DR-001, DR-004, DR-005, DR-006, DR-007 all marked `verified` in the defect log — the last two closed 2026-10-18 once the author supplied R-10's score and ASM-01's real hardware status.
4. **The review report is written, dated, and committed.** This document.

**Baseline declared 2026-10-18.** The two items originally carried forward (DR-005's risk score, DR-006/ASM-01's overdue hardware check) were both closed the same day — see `docs/baseline.md`.
