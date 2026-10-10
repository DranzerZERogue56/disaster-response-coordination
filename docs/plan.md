# Work Breakdown, Schedule & Burn-Down — Disaster Response Coordination

Version: v1.0   Date: 2026-10-10   Status: baselined — fits plannable capacity with 0.8h to spare

**Machine-checkable source:** [`docs/wbs.csv`](wbs.csv) — the tables below are generated from it, not typed by hand twice, so they can't drift apart. Verify with:
`tools/plan-check.py docs/wbs.csv --capacity 15,15,15,15,15,15,20,20,20 --exclude T-2.1b,T-3.3,T-10.2,T-12.4,T-11.2,T-11.3`

## 1. Rules this plan obeys

- **The 100 percent rule.** The 12 work packages below sum to all of the remaining build work implied by `docs/architecture.md` and `PROJECT.md` — if it's not in the WBS, it's not in the plan.
- **Task size: 1–6 hours.** Every task below needs real O/M/P estimates that land in that range; anything that doesn't fit gets split before estimation finishes.
- **Every task traces.** A requirement identifier from `docs/requirements.md`, or `-` for enabling/infrastructure work (and the table says what it enables).
- **Every task has a done-when.** One verifiable sentence, already written for all 38 tasks below.

## 2. Capacity — Weeks 8–16

Real deliverables for each week, pulled from `CALENDAR.md` (not invented):

| Week | Dates | Course overhead this week | Available for this plan |
|---|---|---|---:|
| 8 | Oct 12–18 | Week 8 Quiz, Design Review Checkpoint (Weeks 1-8) | 15 |
| 9 | Oct 19–25 | Milestone 9 — Walking Skeleton & CI, Week 9 Quiz | 15 |
| 10 | Oct 26–Nov 1 | Milestone 10 — Core Increment & Demo, Week 10 Quiz | 15 |
| 11 | Nov 2–8 | Milestone 11 — Test Plan & Defect Log, Week 11 Quiz | 15 |
| 12 | Nov 9–15 | Milestone 12 — Integrated Release Candidate, Week 12 Quiz | 15 |
| 13 | Nov 16–22 | Milestone 13 — Documentation Set, Week 13 Quiz | 15 |
| 14 | Nov 23–29 | Milestone 14 — Deployable Release v1.0, Week 14 Quiz, **Thanksgiving break Wed–Fri** | 20 |
| 15 | Nov 30–Dec 6 | Milestone 15 — Presentation Deck & Rehearsal, Week 15 Quiz | 20 |
| 16 | Dec 7–13 | Week 16 Quiz, Final Submission (Thu Dec 10), Presentation (Fri Dec 11), **finals week** | 20 |
| **Total** | | | **150** |

**This is a deliberate capacity increase, not the course's own suggested pace.** The assignment's own framing names roughly 87 hours as the default (9.7h/week average); this plan commits to 15h/week through the build phase and 20h/week in Weeks 14–16 (deployment, presentation prep, and finals week — chosen heavier because those weeks' own course overhead is lighter per deliverable than the construction weeks, leaving more real hours available), averaging 16.7h/week. That's a real, stated commitment — not padding, and not a hope.

Declared project buffer: **25%** of available hours = **37.5 h**
Plannable effort (available − buffer) = **112.5 h**

## 3. Work breakdown

12 work packages, 38 tasks — proposed by the assistant per this week's AI policy ("may propose tasks," "may not supply durations"). O/M/P columns are blank by design; fill them in, work package by work package.

**T = `_` means not yet estimated.** `tools/plan-check.py` will reject the file until every O/M/P cell is a real number with O ≤ M ≤ P.

### WP-1 — Data Layer & Seed Data  ·  requirements NFR-PRIV-01, NFR-SEC-03  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-1.1 | Thin Python data-access module over the 8 tables | - | 2 | 3 | 5 | 3.17 | A unit test inserts and reads back one row per table with no raw SQL in calling code | — |
| T-1.2 | Purge Job as a real runnable script | NFR-PRIV-01 | 2 | 4 | 6 | 4.00 | Running it against a seeded DB with now_override deletes exactly the expired rows and leaves scenario_runs/dispatcher_accounts untouched | T-1.1 |
| T-1.3 | Synthetic seed-data generator for data/synthetic/ | NFR-SEC-03 | 3 | 5 | 8 | 5.17 | Running the generator produces N reports all tagged synthetic:true and a check script validates all of them | T-1.1 |

### WP-2 — LLM Client  ·  requirements FR-AGENT-01, FR-DEGRADE-02, FR-INFER-01, FR-INFER-02, FR-INFER-03  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-2.1a | LLM Generate interface (Ollama connection, prompt in, response out) | FR-INFER-01, FR-INFER-02 | 3 | 5 | 7.5 | 5.08 | A call against a running Ollama instance with llama3.2:3b returns a schema-valid object for one hand-written test prompt | T-1.1 |
| T-2.1b | Startup hardware capability check | FR-INFER-03 | 1 | 1 | 2 | 1.17 | The check exits cleanly with a clear message before any model load attempt on underspec hardware | — |
| T-2.2 | Hand-rolled output-schema validator + one retry | FR-AGENT-01 | 1 | 2 | 3 | 2.00 | Feeding a deliberately malformed JSON string triggers exactly one retry then a defined error | T-2.1a |
| T-2.3 | FR-DEGRADE-02 fallback chain (smaller model to rules-based to manual) | FR-DEGRADE-02 | 3 | 5 | 8 | 5.17 | Forcing a MODEL_UNAVAILABLE error on the primary model produces a flagged non-LLM proposal via the rules-based path | T-2.2 |

*T-2.1 was split into T-2.1a/T-2.1b on 2026-10-06 — the original bundled estimate (4/7/11, E=7.17h) broke the 1–6h task-size rule, per §1.*

### WP-3 — Intake & Scenario Reader  ·  requirements FR-INTAKE-01, FR-INTAKE-02, FR-INTAKE-03, FR-SIM-01, NFR-REL-03  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-3.1 | Submit Incident Report (validation + field errors) | FR-INTAKE-01, FR-INTAKE-02 | 2 | 4 | 7 | 4.17 | 5 hand-written malformed reports each return the correct named-field error | T-1.1 |
| T-3.2 | Offline queue + reconnection drain in timestamp order | FR-INTAKE-01, NFR-REL-03 | 3 | 5 | 9 | 5.33 | Simulating a network-down flag queues 10 reports; flipping it delivers all 10 in timestamp order | T-3.1 |
| T-3.3 | Duplicate-report detection and merge | FR-INTAKE-03 | 2 | 4 | 7 | 4.17 | Two reports within 1 block/10 minutes with a matching address merge into one incident record | T-3.1 |
| T-3.4 | Scenario Reader (Play Scenario interface) | FR-SIM-01 | 3 | 5 | 8 | 5.17 | Replaying one prewritten scenario file produces the exact same ordered sequence of report submissions on two separate runs | T-2.1a, T-3.1 |

### WP-4 — Resource Agents & Classification  ·  requirements FR-AGENT-01, FR-AGENT-02, FR-AGENT-04  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-4.1 | Classify & Propose for one resource-agent role | FR-AGENT-01, FR-AGENT-02 | 2 | 3 | 4 | 3.00 | 10 seeded reports each receive a severity tag and a proposal with a confidence score within the target latency | T-2.1a, T-3.1 |
| T-4.2 | Extend Classify & Propose to the remaining three roles | FR-AGENT-01, FR-AGENT-02 | 2 | 3 | 5 | 3.17 | All four role types independently classify and propose against role-appropriate seeded reports | T-4.1 |
| T-4.3 | ~60s reasoning timeout + non-LLM fallback trigger | FR-AGENT-04 | 1 | 2 | 3 | 2.00 | Artificially delaying a model response past 60s triggers the documented fallback and logs a TIMEOUT error | T-2.3, T-4.1 |

### WP-5 — Negotiation & Resource Registry  ·  requirements FR-COORD-01, FR-COORD-02, FR-COORD-03, FR-DEGRADE-01, FR-RES-01, FR-RES-03  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-5.1 | Resource/Unit Registry reserve/release/get_status | FR-RES-01, FR-RES-03 | 2 | 3 | 5 | 3.17 | The real (non-spike) registry module passes the same assertions Spike SP-02's script already validated | T-1.1 |
| T-5.2 | Agent-node heartbeat + 30s not-responding detection | FR-DEGRADE-01 | 2 | 3 | 5 | 3.17 | Stopping a simulated node's heartbeat for 31 seconds flips its status to not_responding and notifies | T-5.1 |
| T-5.3 | Resolve Negotiation Conflict (severity/richness/reported-first tiebreak) | FR-COORD-01, FR-COORD-03 | 2 | 3 | 4 | 3.00 | 5 hand-crafted conflicting-proposal pairs each resolve to the documented winner | T-5.1, T-4.2 |
| T-5.4 | Partial-view reconciliation (newer-timestamp-wins) | FR-COORD-02 | 2 | 4 | 6 | 4.00 | Two agents given different-timestamped data for one incident converge on the newer record after reconciliation runs | T-5.3 |

### WP-6 — Approval, Audit & Override  ·  requirements FR-AGENT-03, FR-AUDIT-01, FR-AUDIT-02, FR-INFER-04, FR-RES-02, NFR-SEC-02  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-6.1 | Log Decision (append-only proposal/override log) | FR-AUDIT-01, FR-AUDIT-02, FR-INFER-04 | 2 | 3 | 5 | 3.17 | An UPDATE or DELETE against a logged row is rejected by the database layer itself | T-1.1 |
| T-6.2 | Decide Proposal auto-path + ADR 0006 batch stand-in policy | FR-AGENT-03, NFR-SEC-02 | 2 | 3 | 4 | 3.00 | The 5 confidence/severity cases from NFR-SEC-02's own worked example each route to the documented outcome | T-6.1, T-4.2 |
| T-6.3 | Override Assignment (reason-required + follow-up window) | FR-RES-02 | 2 | 3 | 5 | 3.17 | An override submitted with an empty reason is rejected; one with a reason logs elapsed-time-since-escalation correctly | T-6.1 |

### WP-7 — Dispatcher Web UI  ·  requirements FR-AUTH-01, NFR-ACC-01, NFR-ACC-02, NFR-USE-01  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-7.1 | Pending-proposals list view + polling fallback | NFR-USE-01 | 3 | 4 | 7 | 4.33 | A seeded escalated proposal appears in the UI within 10 seconds of being created | T-6.2 |
| T-7.2 | Approve/modify/reject/override controls (keyboard-only) | NFR-ACC-01 | 2 | 3 | 4 | 3.00 | Completing all four actions on one seeded proposal with the mouse unplugged succeeds with visible focus at every step | T-7.1 |
| T-7.3 | Severity rendered as text alongside color | NFR-ACC-02 | 1 | 2 | 3 | 2.00 | Viewing the UI in grayscale all 5 severity levels are still correctly identifiable by text label | T-7.1 |
| T-7.4 | Dispatcher login/session + role enforcement | FR-AUTH-01 | 2 | 3 | 4 | 3.00 | An observer-role session attempting an override is blocked and the attempt is logged | T-6.1 |

### WP-8 — Notifications  ·  requirements FR-ALERT-01, FR-ALERT-02  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-8.1 | Notify Responder + reserved acknowledgment column | FR-ALERT-01, FR-ALERT-02 | 1 | 2 | 3 | 2.00 | A finalized assignment produces exactly one notification row; the acknowledged_at column exists and accepts a manually-set timestamp | T-6.2 |

### WP-9 — Roster Competition & Scoring  ·  requirements enabling work (PROJECT.md Roster Competition / Evaluation)  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-9.1 | Team-size config loader + scenario_runs orchestration | - | 2 | 4 | 6 | 4.00 | Launching one batch run with a given team_size_config produces exactly the right number of unit/agent_node rows | T-5.1, T-3.4 |
| T-9.2 | Five-measure effectiveness score + naive-baseline comparison | - | 2 | 4 | 6 | 4.00 | Scoring one completed run produces all five sub-measures plus one combined score and a comparable baseline score from logged data only | T-9.1, T-6.1 |
| T-9.3 | Disruption injectors (road closure, unit failure, incident surge) | - | 2 | 3 | 4 | 3.00 | Injecting each disruption type mid-run visibly changes at least one in-flight proposal or reservation | T-9.1, T-5.3 |

### WP-10 — Report & Visualization  ·  requirements FR-MAP-01 (plus PROJECT.md Report generation)  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-10.1 | Markdown report template + fill-in script | - | 2 | 3 | 5 | 3.17 | Running it against one completed scenario_run produces a report with all five required sections | T-9.2 |
| T-10.2 | Post-run static image (Matplotlib + synthetic location graph) | FR-MAP-01 | 1 | 2 | 4 | 2.17 | One completed run produces one saved image file showing the final zone/unit state | T-9.1 |

### WP-11 — Testing  ·  requirements FR-RES-03, FR-SIM-01 (plus PROJECT.md's 4-layer test pyramid)  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-11.1 | Unit tests on core negotiation logic | - | 2 | 3 | 5 | 3.17 | The test suite covers every tiebreak branch and passes in CI | T-5.3 |
| T-11.2 | Scenario-replay regression test on one fixed scenario | FR-SIM-01 | 1 | 2 | 4 | 2.17 | Running the same scenario twice produces byte-identical scoring output | T-9.2 |
| T-11.3 | Property/fuzz test: a resource is never double-booked | FR-RES-03 | 2 | 3 | 5 | 3.17 | A randomized-input fuzz run of 1,000 proposal attempts never produces two live reservations on one unit | T-5.1 |
| T-11.4 | Structural check on Scenario Reader output | FR-SIM-01 | 1 | 2 | 3 | 2.00 | Feeding 10 malformed scenario texts to the checker correctly rejects all 10 before they reach the simulation | T-3.4 |

### WP-12 — Docs, CI & Demo Prep  ·  requirements NFR-MNT-01, NFR-SEC-04  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-12.1 | README clean-machine test | NFR-MNT-01 | 1 | 2 | 3 | 2.00 | A clean clone reaches a running app in under 5 minutes using only the README | T-1.1,T-2.1a,T-2.1b,T-3.1,T-4.1,T-5.1,T-6.1,T-7.1,T-8.1,T-9.1,T-10.1,T-11.1 |
| T-12.2 | Automate the secret scan in CI | NFR-SEC-04 | 1 | 2 | 3 | 2.00 | A CI run on a commit containing a fake API key fails the build | — |
| T-12.3 | Author 3-5 pre-written demo scenarios | - | 2 | 4 | 6 | 4.00 | Each scenario file passes the structural check and produces a non-empty run | T-11.4 |
| T-12.4 | Record the post-run visualization into a short demo clip | - | 1 | 2 | 3 | 2.00 | One scenario's run produces a viewable short clip with no live network dependency at playback time | T-10.2 |

`E = (O + 4M + P) / 6`  ·  spread `P / O` over 4 means: spike it or split it.

## 4. Roll-up

Output of `tools/plan-check.py docs/wbs.csv --capacity 15,15,15,15,15,15,20,20,20 --exclude T-2.1b,T-3.3,T-10.2,T-12.4,T-11.2,T-11.3` — 6 tasks deferred this week (§7) are excluded from the active total, same mechanism the assignment's own Hints section names ("model the cut before you make it"). All 39 tasks are still in `docs/wbs.csv`, marked `status=deferred`, not deleted.

| Work package | Active tasks | Raw E (h) | Calibrated (h) |
|---|---:|---:|---:|
| WP-1 Data Layer & Seed Data | 3 | 12.3 | 12.3 |
| WP-2 LLM Client | 3 | 12.2 | 12.2 |
| WP-3 Intake & Scenario Reader | 3 | 14.7 | 14.7 |
| WP-4 Resource Agents & Classification | 3 | 8.2 | 8.2 |
| WP-5 Negotiation & Resource Registry | 4 | 13.3 | 13.3 |
| WP-6 Approval, Audit & Override | 3 | 9.3 | 9.3 |
| WP-7 Dispatcher Web UI | 4 | 12.3 | 12.3 |
| WP-8 Notifications | 1 | 2.0 | 2.0 |
| WP-9 Roster Competition & Scoring | 3 | 11.0 | 11.0 |
| WP-10 Report & Visualization | 1 | 3.2 | 3.2 |
| WP-11 Testing | 2 | 5.2 | 5.2 |
| WP-12 Docs, CI & Demo Prep | 3 | 8.0 | 8.0 |
| **Total (active)** | **33** | **111.8** | **111.8** |
| Deferred (6 tasks, §7) | 6 | 14.85 | — |
| **Full WBS** | **39** | **126.6** | — |

Rough P80 on the active total (calibrated + 0.84 sd): **114.5 h**

Calibration factor from `docs/hours-log.csv`: **1.00×** — 0 tasks from this WBS are finished yet (construction hasn't started; Milestones 1–7 were planning/design work, not these tasks). The script itself flags this: "thin sample - trust it loosely." This factor gets recomputed for real once Milestone 9's walking skeleton produces the first finished tasks.

## 5. Schedule

Aligned to each week's own graded milestone name from `CALENDAR.md`, not just raw dependency order — the two turned out to match well, since the course's own cadence (walking skeleton in Week 9, test plan in Week 11, integration in Week 12, documentation in Week 13) is basically the same sequencing the dependency graph in `docs/wbs.csv` would produce on its own.

| Week | Work packages in flight | Planned hours | Gate |
|---|---|---:|---|
| 8 | WP-1 start (T-1.1) | 15 | Milestone 8 design review passed; `architecture.md` baselined, change control active from here |
| 9 | WP-1 finish, WP-2, CI setup (T-12.2) | 15 | CI green on a thin end-to-end slice touching every container box (Milestone 9, Walking Skeleton) |
| 10 | WP-3, WP-4 start | 15 | One resource-agent role classifies a real report end to end, demoable (Milestone 10) |
| 11 | WP-4 finish, WP-5 start, WP-11 start | 15 | A written test plan exists; core negotiation logic has its first passing unit tests (Milestone 11) |
| 12 | WP-5 finish, WP-6, WP-11 continue | 15 | Full report → proposal → decide → assign chain works end to end for all 4 roles, no manual steps (Milestone 12) |
| 13 | WP-8, WP-12 docs (T-12.1), WP-11 finish | 15 | Clean-machine test passes in under 5 minutes (Milestone 13, Documentation Set & Clean-Machine Test) |
| 14 | WP-7, WP-9, WP-10 start | 20 | Interactive and batch modes both run a full scenario unattended (Milestone 14, Deployable Release). **Last week anything new starts.** |
| 15 | WP-10 finish, WP-12 finish | 20 | Demo scenarios run cleanly; report + visualization generated from a real run (Milestone 15, Presentation Deck & Rehearsal) |
| 16 | Buffer / polish only — nothing new | 20 | Final submission and presentation ready |

Rules followed: risky work first (WP-1, WP-2 start immediately; WP-5 — the multi-process heartbeat work risk R-01 flags as the project's biggest technical unknown — starts Week 11, not left for late); integration lands at Week 12, matching the course's own Integrated Release Candidate milestone; nothing new starts after Week 14.

## 6. Burn-down baseline

Output of `tools/plan-check.py docs/wbs.csv --capacity 15,15,15,15,15,15,20,20,20 --exclude T-2.1b,T-3.3,T-10.2,T-12.4,T-11.2,T-11.3`:

| Week | Capacity | Ideal remaining | Projected remaining |
|---|---:|---:|---:|
| 8 | 15.0 | 112.5 | 111.8 |
| 9 | 15.0 | 101.2 | 96.8 |
| 10 | 15.0 | 90.0 | 81.8 |
| 11 | 15.0 | 78.8 | 66.8 |
| 12 | 15.0 | 67.5 | 51.8 |
| 13 | 15.0 | 56.2 | 36.8 |
| 14 | 20.0 | 45.0 | 21.8 |
| 15 | 20.0 | 30.0 | 1.8 |
| 16 | 20.0 | 15.0 | -18.2 |
| end | — | 0.0 | -38.2 |

**VERDICT: fits, with 0.8h to spare** against the 112.5h plannable (buffered) threshold — not just inside raw capacity this time, inside the buffered one. The projected line stays at or under the ideal line every week from Week 8 onward (111.8 ≤ 112.5 from the very first row), so the declared 37.5h buffer is never touched by the base plan itself — the full buffer is available if risk R-06 or R-07 actually fires, which was not true of the earlier 150h-capacity-only version of this plan (that version ate 14.1h of the buffer before Week 8 even started). This is the direct result of §7's deferral decision, made after the capacity increase alone wasn't enough.

## 7. The scope decision

The plan started 70.8h over a default 87h/9.7h-week capacity. Three decisions closed the gap completely: a re-estimation pass, a real capacity increase, and — once those two together still left 14.1h unclosed — six tasks actually deferred to Won't-this-release or pushed past Week 16.

| Cut / deferred / re-estimated | Item | Reqs | Hours recovered | MoSCoW before → after | Why |
|---|---|---|---:|---|---|
| re-estimated | T-4.1 Classify & Propose (one role) | FR-AGENT-01, FR-AGENT-02 | 2.17 | Must → Must | Reviewed against the sorted-by-effort list; original estimate was hedging, not real difficulty |
| re-estimated | T-5.3 Resolve Negotiation Conflict | FR-COORD-01, FR-COORD-03 | 2.17 | Must → Must | Same review — a deterministic, fully-specified tiebreak rule doesn't need a generous pessimistic case |
| re-estimated | T-9.3 Disruption injectors | - | 2.17 | Should → Should | Same review |
| re-estimated | T-6.2 Decide Proposal + ADR 0006 | FR-AGENT-03, NFR-SEC-02 | 1.00 | Must → Must | Same review |
| re-estimated | T-7.2 Approve/modify/reject/override controls | NFR-ACC-01 | 1.00 | Must → Must | Same review |
| re-estimated | T-7.4 Dispatcher login/session | FR-AUTH-01 | 1.00 | Should → Should | Same review |
| capacity increase | Weeks 8-16 availability raised from 87h (9.7h/week default) to 150h (16.7h/week average, 15h build weeks / 20h Weeks 14-16) | all | 63.0 (vs. default capacity) | n/a | A deliberate, stated commitment to work more than the course's suggested pace — chosen over cutting the Dispatcher Web UI or any Must-priority feature, since neither was cheap enough to be worth it for the hours it would have recovered |
| **deferred** | **T-2.1b** Startup hardware capability check | **FR-INFER-03** | **1.17** | **Should → Won't** | A failed model load still surfaces an error via FR-DEGRADE-02's fallback chain; losing the clean preflight message is a real but small cost |
| **deferred** | **T-3.3** Duplicate-report detection and merge | **FR-INTAKE-03** | **4.17** | **Should → Won't** | The `incident_reports` schema already supports it (`duplicate_of_id`); cheap to pick back up, costly to build and test properly this week |
| **deferred** | **T-10.2** + **T-12.4** Zone-display image + its demo clip | **FR-MAP-01** | **4.17** | **Should → Won't** | Already named in the requirement's own Week-4 rationale as "the first thing to slip if time gets tight" — this is that slip, acted on rather than just predicted |
| **deferred** | **T-11.2** Scenario-replay regression test | FR-SIM-01 (stays Must — the *feature* is unaffected, only this extra test) | **2.17** | n/a (test coverage, not the requirement) | FR-SIM-01 is still built by T-3.4 this week; this specific regression test moves to Milestone 11 (Test Plan week), where it belongs anyway |
| **deferred** | **T-11.3** Property/fuzz test (no double-booking) | FR-RES-03 (stays Must — the *feature* is unaffected, only this extra test) | **3.17** | n/a (test coverage, not the requirement) | FR-RES-03's core guarantee already has real evidence behind it — Spike SP-02, 20/20 trials, zero double-bookings — so this automated test is confirmatory, not load-bearing, and can wait for Milestone 11 |
| ~~accepted overage~~ | ~~14.1h beyond plannable~~ | | | | **Superseded below — closed, not accepted.** |

**Result: the plan now fits.** 111.8h raw against 112.5h plannable (25% buffer, 150h capacity) — 0.8h to spare, not a 14.1h overage. See §4 and §6 for the recomputed roll-up and burn-down.

**`docs/requirements.md` update:** FR-INTAKE-03, FR-INFER-03, and FR-MAP-01 moved from Should to Won't (this release), v1.2 → v1.3, each with a scope-decision note pointing back here. T-11.2 and T-11.3's underlying requirements (FR-SIM-01, FR-RES-03) are **not** touched — they stay Must and are still built this plan, just verified by fewer automated tests until Milestone 11. The requirements already marked out of scope in Milestone 6 (FR-COORD-04, FR-MAP-02, NFR-PORT-01) remain unchanged; see `docs/architecture.md` §1.

Signed: Dranzer Rogue, 2026-10-07 (re-baselined 2026-10-10 to close the residual gap). Re-baselined after any change of more than 5 hours.

---

## Medium Tier (extra credit)

Four items, each computed from numbers already on the record (the scored WBS and risk register), not new duration judgment calls.

### A dependency graph and critical path

Diagram: [`docs/diagrams/wp-dependencies.dot`](diagrams/wp-dependencies.dot) + [`wp-dependencies.png`](diagrams/wp-dependencies.png) — finish-to-start dependencies at the work-package level, computed directly from `docs/wbs.csv`'s `depends_on` column (not hand-drawn).

**Critical path (longest E-weighted chain, active tasks only): WP-1 → WP-2 → WP-3 → WP-4 → WP-5 → WP-9 → WP-10 → WP-12, 82.92h.** (Recomputed 2026-10-10 after §7's deferral decision — shorter than the original 97.58h mainly because WP-11's deferred tasks, T-11.2/T-11.3, no longer compete for the critical slot into WP-12; WP-10's remaining task carries that edge instead.)

**What this means for a solo builder — and where the standard definition misleads here:** in a team setting, the critical path is the one chain that sets the project's minimum completion date, because non-critical work happens in parallel on someone else's hours and absorbs delay for free. There is no second person here. Every hour on WP-6, WP-7, WP-8, and WP-11 — the work packages *not* on this chain — still has to be spent by the same one developer, so total calendar time is bounded by the **full active 111.8h**, not the 82.92h critical path. The critical-path number is still useful, just not for the reason a textbook says: it shows which work packages have **zero slack and the most fan-out**. WP-1 (data layer) and WP-2 (LLM client) sit at the root with the most downstream dependents — a slip there propagates to nearly everything else, including work packages not formally "on" the critical path. WP-8 (Notifications, 2.0h, nothing depends on it) can slip freely with no ripple at all. The real scheduling lesson from this graph isn't "protect the critical path," it's "protect the root" — which is exactly why `docs/plan.md` §5 schedules WP-1 and WP-2 first.

### A P50 / P80 range for the whole plan

Computed from the PERT standard deviation of every task (`sd = (P − O) / 6`), summed as variance (`sd²`) across the 33 active tasks (deferred tasks excluded, same as §4), per `docs/wbs.csv`:

| | Hours |
|---|---:|
| P50 (the calibrated active total itself) | 111.75 |
| Total variance (Σ sd²) | 10.45 |
| √variance (sd of the sum) | 3.23 |
| **P80 (P50 + 0.84·sd)** | **114.47** |

The P50-to-P80 spread is only 2.72h — narrow, because most task spreads in this plan are tight (most `P/O` ratios sit well under 4, by design, after the re-estimation pass). **The honest caveat, stated and not glossed over:** this roll-up assumes every task's uncertainty is independent. It isn't. If the real risk is R-01 (Mesa's first-ever multi-process configuration) going wrong, that doesn't cost one task 2-5 extra hours in isolation — it correlates across T-5.2, T-9.1, and T-11.x all at once, since they all sit downstream of the same wrong assumption. The real uncertainty in this plan is dominated by a handful of correlated architectural unknowns (R-01, R-02, R-04), not by 39 independent coin flips, so P80 here is a **floor** on the real uncertainty, not a ceiling — the quantified risk reserve below is a better estimate of what a single bad assumption could actually cost.

### Quantified risk reserve

Top 5 risks by exposure (`docs/risk-register.md`), reserve = probability × impact-hours. Likelihood converted to probability on a standard 5-point scale (L1=10%, L2=30%, L3=50%, L4=70%, L5=90%); impact converted to its band midpoint (I1=1h, I2=3.5h, I3=8.5h, I4=18.5h, I5=30h) — both conventions stated here so the arithmetic is checkable, not asserted:

| Risk | L (prob.) | I (midpoint) | Reserve |
|---|---|---|---:|
| R-05 (became an issue, resolved 2026-10-10) | 5 (90%) | 2 (3.5h) | 3.15h |
| R-07 (optimism bias) | 3 (50%) | 3 (8.5h) | 4.25h |
| R-01 (Mesa multi-process) | 4 (70%) | 2 (3.5h) | 2.45h |
| R-04 (GPU hardware) | 4 (70%) | 2 (3.5h) | 2.45h |
| R-06 (solo-dev schedule) | 4 (70%) | 2 (3.5h) | 2.45h |
| **Total quantified reserve** | | | **14.75h** |

This is a separate number from the 25% schedule buffer (§2) — the schedule buffer absorbs general estimation looseness across the active tasks, while this reserve is specifically sized against the five named, scored things most likely to actually go wrong. R-05 stays in the top five even though it's now retired for this milestone (§7 closed it): the underlying pattern — a WBS outgrowing capacity — is exactly the kind of thing that recurs in Milestone 9 once real construction tasks get added, so its exposure score still earns its place in the reserve rather than being dropped for looking resolved today.

### Plan-on-a-page

**Disaster Response Coordination — Milestone 7 at a glance (2026-10-10, final)**

- **Scope:** 12 work packages, 39 tasks total — 33 active, 6 deferred. Active: 111.75h raw (P50) / 114.47h (P80)
- **Capacity:** 150h, Weeks 8-16 (15h build weeks, 20h Weeks 14-16) — a stated increase over the course's 87h default
- **Buffer:** 25% (37.5h declared, fully intact — the plan fits inside the buffered threshold, not just raw capacity)
- **Critical path:** WP-1 → WP-2 → WP-3 → WP-4 → WP-5 → WP-9 → WP-10 → WP-12, 82.92h — protect the root (WP-1/WP-2), not just the chain
- **Verdict:** fits, with 0.8h to spare against the 112.5h plannable threshold
- **Top 5 risks (exposure):** R-05 scope, fired and resolved (10) · R-07 optimism bias (9) · R-01 Mesa multi-process (8) · R-04 GPU hardware (8) · R-06 solo-dev schedule (8)
- **Quantified reserve against those five:** 14.75h — now fully inside the untouched 37.5h buffer, not competing with it
- **Scope decision:** 9.5h recovered by re-estimation, 63h by a real capacity increase, 14.85h by deferring 6 tasks (3 requirements moved Should → Won't: FR-INTAKE-03, FR-INFER-03, FR-MAP-01; 2 tasks deferred test coverage on Must features already backed by real evidence)
- **Ship confidence:** green for this plan's internal arithmetic — it fits, the buffer is untouched, every number traces to a real decision. Still amber on execution risk: the plan has never been tested against real completed work (calibration factor is 1.00×, 0 samples) — that's Milestone 9's job, not this week's
