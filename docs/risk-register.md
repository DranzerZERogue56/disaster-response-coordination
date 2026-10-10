# Risk Register — Disaster Response Coordination

Review this every Monday. A register written once is a document; reviewed weekly, it's a control.

## Scales

**Likelihood** — 1 rare · 2 unlikely · 3 even odds · 4 likely · 5 near certain, before doing anything about it.

**Impact** — in hours you'd lose: 1 = under 2h · 2 = 2–5h · 3 = 5–12h · 4 = 12–25h · 5 = over 25h, or the project can't ship.

**Exposure** = Likelihood × Impact. Sorted descending below.

**Response** — avoid (change the plan so it can't happen) · mitigate (reduce likelihood or impact) · transfer (make it someone else's problem) · accept (name it, write the contingency, move on).

---

**R-05** — Because the full work breakdown (WP-1 through WP-12, 39 tasks) was built before calibration, it described meaningfully more work than the remaining plannable hours could hold.
· scope · L 5 · I 2 · **E 10**
· **Trigger:** the calibrated plan total (§4 of `docs/plan.md`) exceeds plannable capacity.
· **Owner:** me.
· **Response:** mitigate, then avoid — applied in two passes: (1) 2026-10-07: 6 tasks re-estimated after a second look (9.5h recovered), capacity raised from the course's default 87h to a real, stated 150h commitment (63h recovered), closing the original 70.8h gap to a 14.1h residual, accepted at the time. (2) 2026-10-10: revisited for full marks — 6 tasks deferred to Won't-this-release or pushed to Milestone 11 (14.85h recovered, `docs/plan.md` §7), closing the residual gap completely. Plan now fits with 0.8h to spare.
· **Contingency:** no longer needed for this instance — the gap is closed, not accepted. `docs/requirements.md` v1.3 records the three Won't changes (FR-INTAKE-03, FR-INFER-03, FR-MAP-01).
· **Status:** **became an issue on 2026-10-07; resolved on 2026-10-10.** Retired for this milestone's WBS. Re-opens if Milestone 9's first real tasks add scope on top of this plan without a matching deferral or capacity adjustment — the same pattern, not a new risk.

**R-07** — Because this is the first time estimation has been done at this project's scale, optimism bias may produce systematically low estimates across many tasks rather than one or two outliers.
· schedule/personal · L 3 · I 3 · **E 9**
· **Trigger:** the calibration pass (`docs/plan.md` §4) computes a factor greater than 1.3× from the first several completed Milestone-7-onward tasks.
· **Owner:** me.
· **Response:** mitigate — re-apply the calibration factor to every remaining task estimate immediately once computed, not after a second data point. Already partly addressed this week: 6 of the highest-effort estimates were re-reviewed and tightened after seeing the full sorted list, rather than accepted at face value.
· **Contingency:** re-run the scope decision with the recalibrated total.
· **Status:** open.

**R-01** — Because Mesa has never been run in a multi-process configuration before (one node per role-type, per `docs/architecture.md` §6), implementing agent-node heartbeat detection across separate OS processes (T-5.2) may take meaningfully longer than a single-process design would have.
· technical/novelty · L 4 · I 2 · **E 8**
· **Trigger:** T-5.2 passes its first logged session without a working heartbeat loop.
· **Owner:** me.
· **Response:** mitigate — timebox a 2-hour spike on cross-process heartbeat signaling before committing further hours to T-5.2. Scheduled early (Week 11, `docs/plan.md` §5) rather than left for late, specifically because this risk is rated likely.
· **Contingency:** fall back to a single-process simulated "node" model (threads, not OS processes), and document the narrower decentralization claim in a new ADR.
· **Status:** open.

**R-04** — Because the GPU server hardware isn't acquired yet (`docs/requirements.md` CON-04, `HARDWARE.md`), every model-dependent task (T-2.1a through T-4.3, T-9.x) can't be fully verified until it arrives.
· dependency · L 4 · I 2 · **E 8**
· **Trigger:** Week 9 begins and the hardware still isn't available.
· **Owner:** me.
· **Response:** mitigate — continue development against the dev laptop's smaller "lower level" model fallback (FR-DEGRADE-02) and scale scenario size down.
· **Contingency:** a paid cloud GPU-hour, scoped strictly to development/testing (never the shipped system), only if Week 10 arrives with still no hardware — a documented, deliberate exception to CON-03.
· **Status:** open.

**R-06** — Because this is a solo, one-developer project with fixed weekly milestone deadlines (CON-02) and no peer coverage, any illness or multi-day unavailability directly removes hours with no substitute.
· schedule/personal · L 4 · I 2 · **E 8**
· **Trigger:** two or more consecutive days with zero logged hours during a non-break week.
· **Owner:** me.
· **Response:** mitigate — the declared project buffer exists specifically to absorb this. Given R-05's status, the real remaining cushion is 23.4h, not the full 37.5h declared — this response is weaker than it looks on paper.
· **Contingency:** if a loss exceeds the remaining 23.4h of real slack, trigger the scope-decision table that same week, not retroactively.
· **Status:** open.

**R-02** — Because the local model hasn't been benchmarked on real hardware yet (`docs/requirements.md` ASM-02 is still unverified), the 5-second classification target (NFR-PERF-01) and the ~60-second reasoning timeout (FR-AGENT-04) may both be unrealistic once the real GPU is in use.
· technical/novelty · L 3 · I 2 · **E 6**
· **Trigger:** the first real benchmark run (T-4.1) logs a p95 classification time over 5 seconds on 5 consecutive attempts.
· **Owner:** me.
· **Response:** mitigate — raise the NFR-PERF-01 threshold with a documented rationale, or promote the rules-based classification path (FR-DEGRADE-02) from fallback to primary for this release.
· **Contingency:** scenario scale (incidents per run) drops until the target is met again.
· **Status:** open.

**R-03** — Because `llama3.2:3b`'s confidence score hasn't been validated for real calibration (Milestone 5's Spike SP-03 is still unrun), the ADR 0006 stand-in threshold (confidence ≥ 60) may misroute a large fraction of batch-mode proposals, putting every roster-competition score built on it in question.
· dependency · L 3 · I 2 · **E 6**
· **Trigger:** SP-03, once run, shows the threshold approving fewer than 50% or more than 95% of escalated test cases — ADR 0006's own revisit trigger.
· **Owner:** me.
· **Response:** mitigate — recalibrate the threshold from SP-03's real distribution before trusting any batch score produced before that point; funded as part of T-6.2.
· **Contingency:** re-run the affected batch competitions after recalibration.
· **Status:** open.

**R-08** — Because NFR-SEC-03 requires every incident report in the repository to be synthetic, an accidental commit of a real address, name, or other identifying detail during demo-scenario authoring (T-12.3) would violate that requirement.
· data/legal · L 2 · I 2 · **E 4**
· **Trigger:** the synthetic-marker check script (built in T-1.3) flags a file outside `data/synthetic/` or missing its marker.
· **Owner:** me.
· **Response:** mitigate — run the check script before every milestone submission, as NFR-SEC-03 itself already specifies as its own measurement method.
· **Contingency:** any flagged commit gets a required git-history scrub before the next push.
· **Status:** open.

**R-09** — Because `llama3.2:3b` ships under a non-standard license (`LicenseRef-Llama3.2-Community`, ADR 0001) rather than a clean permissive one, any future step toward productizing or publicly redistributing this project could trigger the license's 700M-MAU commercial clause or otherwise need a licensing review not yet done.
· data/legal · L 1 · I 2 · **E 2**
· **Trigger:** any concrete step toward deployment beyond the Week 16 academic submission (e.g. a real agency expressing interest, per `docs/requirements.md` ASM-05).
· **Owner:** me.
· **Response:** escalate — re-verify the model license at its primary source before any such step.
· **Contingency:** swap to `mistral:7b` (Apache-2.0, already scored as ADR 0001's documented runner-up) if the review requires it.
· **Status:** open.

---

Categories represented: technical/novelty (R-01, R-02), dependency (R-03, R-04), scope (R-05), schedule/personal (R-06, R-07), data/legal (R-08, R-09) — all five, not just the two the rubric requires.

**Top five by exposure (work these first):** R-05 (10), R-07 (9), R-01 (8), R-04 (8), R-06 (8).
