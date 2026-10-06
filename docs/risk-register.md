# Risk Register — Disaster Response Coordination

Review this every Monday. A register written once is a document; reviewed weekly, it's a control.

## Scales

**Likelihood** — 1 rare · 2 unlikely · 3 even odds · 4 likely · 5 near certain, before doing anything about it.

**Impact** — in hours you'd lose: 1 = under 2h · 2 = 2–5h · 3 = 5–12h · 4 = 12–25h · 5 = over 25h, or the project can't ship.

**Exposure** = Likelihood × Impact. Sorted descending once scored.

**Response** — avoid (change the plan so it can't happen) · mitigate (reduce likelihood or impact) · transfer (make it someone else's problem) · accept (name it, write the contingency, move on).

**L / I / E are not filled in below — those are the author's call, same as task hours, not something an assistant supplies.**

---

**R-01** — Because Mesa has never been run in a multi-process configuration before (one node per role-type, per `docs/architecture.md` §6), implementing agent-node heartbeat detection across separate OS processes (T-5.2) may take meaningfully longer than a single-process design would have.
· technical/novelty · L `_` · I `_` · E `_`
· **Trigger:** T-5.2 passes its first logged session without a working heartbeat loop.
· **Owner:** me.
· **Response:** mitigate — timebox a 2-hour spike on cross-process heartbeat signaling before committing further hours to T-5.2.
· **Contingency:** fall back to a single-process simulated "node" model (threads, not OS processes), and document the narrower decentralization claim in a new ADR.
· **Status:** open.

**R-02** — Because the local model hasn't been benchmarked on real hardware yet (`docs/requirements.md` ASM-02 is still unverified), the 5-second classification target (NFR-PERF-01) and the ~60-second reasoning timeout (FR-AGENT-04) may both be unrealistic once the real GPU is in use.
· technical/novelty · L `_` · I `_` · E `_`
· **Trigger:** the first real benchmark run (T-4.1) logs a p95 classification time over 5 seconds on 5 consecutive attempts.
· **Owner:** me.
· **Response:** mitigate — raise the NFR-PERF-01 threshold with a documented rationale, or promote the rules-based classification path (FR-DEGRADE-02) from fallback to primary for this release.
· **Contingency:** scenario scale (incidents per run) drops until the target is met again.
· **Status:** open.

**R-03** — Because `llama3.2:3b`'s confidence score hasn't been validated for real calibration (Milestone 5's Spike SP-03 is still unrun), the ADR 0006 stand-in threshold (confidence ≥ 60) may misroute a large fraction of batch-mode proposals, putting every roster-competition score built on it in question.
· dependency · L `_` · I `_` · E `_`
· **Trigger:** SP-03, once run, shows the threshold approving fewer than 50% or more than 95% of escalated test cases — ADR 0006's own revisit trigger.
· **Owner:** me.
· **Response:** mitigate — recalibrate the threshold from SP-03's real distribution before trusting any batch score produced before that point; funded as part of T-6.2.
· **Contingency:** re-run the affected batch competitions after recalibration.
· **Status:** open.

**R-04** — Because the GPU server hardware isn't acquired yet (`docs/requirements.md` CON-04, `HARDWARE.md`), every model-dependent task (T-2.1 through T-4.3, T-9.x) can't be fully verified until it arrives.
· dependency · L `_` · I `_` · E `_`
· **Trigger:** Week 9 begins and the hardware still isn't available.
· **Owner:** me.
· **Response:** mitigate — continue development against the dev laptop's smaller "lower level" model fallback (FR-DEGRADE-02) and scale scenario size down.
· **Contingency:** a paid cloud GPU-hour, scoped strictly to development/testing (never the shipped system), only if Week 10 arrives with still no hardware — a documented, deliberate exception to CON-03.
· **Status:** open.

**R-05** — Because the full work breakdown (WP-1 through WP-12, 38 tasks) was built before calibration, it may describe meaningfully more work than the remaining plannable hours can hold — the assignment's own framing already predicts this.
· scope · L `_` · I `_` · E `_`
· **Trigger:** the calibrated plan total (§3 of `docs/plan.md`) exceeds plannable capacity.
· **Owner:** me.
· **Response:** mitigate — apply the scope-decision table to cut or defer the lowest-MoSCoW-priority work first (candidates already flagged: WP-8 notifications, WP-10's image/video polish, WP-9's disruption injectors) before touching any Must-priority work.
· **Contingency:** `docs/requirements.md` gets updated so cut items read Won't, per this milestone's own required deliverable.
· **Status:** open.

**R-06** — Because this is a solo, one-developer project with fixed weekly milestone deadlines (CON-02) and no peer coverage, any illness or multi-day unavailability directly removes hours with no substitute.
· schedule/personal · L `_` · I `_` · E `_`
· **Trigger:** two or more consecutive days with zero logged hours during a non-break week.
· **Owner:** me.
· **Response:** mitigate — the declared project buffer exists specifically to absorb this.
· **Contingency:** if a loss exceeds the buffer, trigger the scope-decision table that same week, not retroactively.
· **Status:** open.

**R-07** — Because this is the first time estimation has been done at this project's scale, optimism bias may produce systematically low estimates across many tasks rather than one or two outliers.
· schedule/personal · L `_` · I `_` · E `_`
· **Trigger:** the calibration pass computes a factor greater than 1.3× from the first several completed Milestone-7-onward tasks.
· **Owner:** me.
· **Response:** mitigate — re-apply the calibration factor to every remaining task estimate immediately once computed, not after a second data point.
· **Contingency:** re-run the scope decision with the recalibrated total.
· **Status:** open.

**R-08** — Because NFR-SEC-03 requires every incident report in the repository to be synthetic, an accidental commit of a real address, name, or other identifying detail during demo-scenario authoring (T-12.3) would violate that requirement.
· data/legal · L `_` · I `_` · E `_`
· **Trigger:** the synthetic-marker check script (built in T-1.3) flags a file outside `data/synthetic/` or missing its marker.
· **Owner:** me.
· **Response:** mitigate — run the check script before every milestone submission, as NFR-SEC-03 itself already specifies as its own measurement method.
· **Contingency:** any flagged commit gets a required git-history scrub before the next push.
· **Status:** open.

**R-09** — Because `llama3.2:3b` ships under a non-standard license (`LicenseRef-Llama3.2-Community`, ADR 0001) rather than a clean permissive one, any future step toward productizing or publicly redistributing this project could trigger the license's 700M-MAU commercial clause or otherwise need a licensing review not yet done.
· data/legal · L `_` · I `_` · E `_`
· **Trigger:** any concrete step toward deployment beyond the Week 16 academic submission (e.g. a real agency expressing interest, per `docs/requirements.md` ASM-05).
· **Owner:** me.
· **Response:** escalate — re-verify the model license at its primary source before any such step.
· **Contingency:** swap to `mistral:7b` (Apache-2.0, already scored as ADR 0001's documented runner-up) if the review requires it.
· **Status:** open.

---

Categories represented: technical/novelty (R-01, R-02), dependency (R-03, R-04), scope (R-05), schedule/personal (R-06, R-07), data/legal (R-08, R-09) — all five, not just the two the rubric requires.
