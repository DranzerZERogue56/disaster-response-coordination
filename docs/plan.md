# Work Breakdown, Schedule & Burn-Down — Disaster Response Coordination

Version: v0.1 (draft)   Date: 2026-10-06   Status: estimates pending

**Machine-checkable source:** [`docs/wbs.csv`](wbs.csv) — the tables below are generated from it, not typed by hand twice, so they can't drift apart. Run `tools/plan-check.py docs/wbs.csv` once every task has real O/M/P hours.

## 1. Rules this plan obeys

- **The 100 percent rule.** The 12 work packages below sum to all of the remaining build work implied by `docs/architecture.md` and `PROJECT.md` — if it's not in the WBS, it's not in the plan.
- **Task size: 1–6 hours.** Every task below needs real O/M/P estimates that land in that range; anything that doesn't fit gets split before estimation finishes.
- **Every task traces.** A requirement identifier from `docs/requirements.md`, or `-` for enabling/infrastructure work (and the table says what it enables).
- **Every task has a done-when.** One verifiable sentence, already written for all 38 tasks below.

## 2. Capacity — Weeks 8–16

Real deliverables for each week, pulled from `CALENDAR.md` (not invented):

| Week | Dates | Course overhead this week | Available for this plan |
|---|---|---|---:|
| 8 | Oct 12–18 | Week 8 Quiz, Design Review Checkpoint (Weeks 1-8) | `_` |
| 9 | Oct 19–25 | Milestone 9 — Walking Skeleton & CI, Week 9 Quiz | `_` |
| 10 | Oct 26–Nov 1 | Milestone 10 — Core Increment & Demo, Week 10 Quiz | `_` |
| 11 | Nov 2–8 | Milestone 11 — Test Plan & Defect Log, Week 11 Quiz | `_` |
| 12 | Nov 9–15 | Milestone 12 — Integrated Release Candidate, Week 12 Quiz | `_` |
| 13 | Nov 16–22 | Milestone 13 — Documentation Set, Week 13 Quiz | `_` |
| 14 | Nov 23–29 | Milestone 14 — Deployable Release v1.0, Week 14 Quiz, **Thanksgiving break Wed–Fri** | `_` |
| 15 | Nov 30–Dec 6 | Milestone 15 — Presentation Deck & Rehearsal, Week 15 Quiz | `_` |
| 16 | Dec 7–13 | Week 16 Quiz, Final Submission (Thu Dec 10), Presentation (Fri Dec 11), **finals week** | `_` |
| **Total** | | | **`_`** |

The assignment's own framing names roughly **87 hours** as what's actually left for *this* plan (coding, not the milestone write-ups themselves) — use that as a sanity check on the weekly split once filled in, not a number to force each row into matching exactly.

Declared project buffer: **`_`%** of available hours = **`_` h**
Plannable effort (available − buffer) = **`_` h**

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
| T-4.1 | Classify & Propose for one resource-agent role | FR-AGENT-01, FR-AGENT-02 | _ | _ | _ | _ | 10 seeded reports each receive a severity tag and a proposal with a confidence score within the target latency | T-2.1a, T-3.1 |
| T-4.2 | Extend Classify & Propose to the remaining three roles | FR-AGENT-01, FR-AGENT-02 | _ | _ | _ | _ | All four role types independently classify and propose against role-appropriate seeded reports | T-4.1 |
| T-4.3 | ~60s reasoning timeout + non-LLM fallback trigger | FR-AGENT-04 | _ | _ | _ | _ | Artificially delaying a model response past 60s triggers the documented fallback and logs a TIMEOUT error | T-2.3, T-4.1 |

### WP-5 — Negotiation & Resource Registry  ·  requirements FR-COORD-01, FR-COORD-02, FR-COORD-03, FR-DEGRADE-01, FR-RES-01, FR-RES-03  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-5.1 | Resource/Unit Registry reserve/release/get_status | FR-RES-01, FR-RES-03 | _ | _ | _ | _ | The real (non-spike) registry module passes the same assertions Spike SP-02's script already validated | T-1.1 |
| T-5.2 | Agent-node heartbeat + 30s not-responding detection | FR-DEGRADE-01 | _ | _ | _ | _ | Stopping a simulated node's heartbeat for 31 seconds flips its status to not_responding and notifies | T-5.1 |
| T-5.3 | Resolve Negotiation Conflict (severity/richness/reported-first tiebreak) | FR-COORD-01, FR-COORD-03 | _ | _ | _ | _ | 5 hand-crafted conflicting-proposal pairs each resolve to the documented winner | T-5.1, T-4.2 |
| T-5.4 | Partial-view reconciliation (newer-timestamp-wins) | FR-COORD-02 | _ | _ | _ | _ | Two agents given different-timestamped data for one incident converge on the newer record after reconciliation runs | T-5.3 |

### WP-6 — Approval, Audit & Override  ·  requirements FR-AGENT-03, FR-AUDIT-01, FR-AUDIT-02, FR-INFER-04, FR-RES-02, NFR-SEC-02  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-6.1 | Log Decision (append-only proposal/override log) | FR-AUDIT-01, FR-AUDIT-02, FR-INFER-04 | _ | _ | _ | _ | An UPDATE or DELETE against a logged row is rejected by the database layer itself | T-1.1 |
| T-6.2 | Decide Proposal auto-path + ADR 0006 batch stand-in policy | FR-AGENT-03, NFR-SEC-02 | _ | _ | _ | _ | The 5 confidence/severity cases from NFR-SEC-02's own worked example each route to the documented outcome | T-6.1, T-4.2 |
| T-6.3 | Override Assignment (reason-required + follow-up window) | FR-RES-02 | _ | _ | _ | _ | An override submitted with an empty reason is rejected; one with a reason logs elapsed-time-since-escalation correctly | T-6.1 |

### WP-7 — Dispatcher Web UI  ·  requirements FR-AUTH-01, NFR-ACC-01, NFR-ACC-02, NFR-USE-01  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-7.1 | Pending-proposals list view + polling fallback | NFR-USE-01 | _ | _ | _ | _ | A seeded escalated proposal appears in the UI within 10 seconds of being created | T-6.2 |
| T-7.2 | Approve/modify/reject/override controls (keyboard-only) | NFR-ACC-01 | _ | _ | _ | _ | Completing all four actions on one seeded proposal with the mouse unplugged succeeds with visible focus at every step | T-7.1 |
| T-7.3 | Severity rendered as text alongside color | NFR-ACC-02 | _ | _ | _ | _ | Viewing the UI in grayscale all 5 severity levels are still correctly identifiable by text label | T-7.1 |
| T-7.4 | Dispatcher login/session + role enforcement | FR-AUTH-01 | _ | _ | _ | _ | An observer-role session attempting an override is blocked and the attempt is logged | T-6.1 |

### WP-8 — Notifications  ·  requirements FR-ALERT-01, FR-ALERT-02  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-8.1 | Notify Responder + reserved acknowledgment column | FR-ALERT-01, FR-ALERT-02 | _ | _ | _ | _ | A finalized assignment produces exactly one notification row; the acknowledged_at column exists and accepts a manually-set timestamp | T-6.2 |

### WP-9 — Roster Competition & Scoring  ·  requirements enabling work (PROJECT.md Roster Competition / Evaluation)  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-9.1 | Team-size config loader + scenario_runs orchestration | - | _ | _ | _ | _ | Launching one batch run with a given team_size_config produces exactly the right number of unit/agent_node rows | T-5.1, T-3.4 |
| T-9.2 | Five-measure effectiveness score + naive-baseline comparison | - | _ | _ | _ | _ | Scoring one completed run produces all five sub-measures plus one combined score and a comparable baseline score from logged data only | T-9.1, T-6.1 |
| T-9.3 | Disruption injectors (road closure, unit failure, incident surge) | - | _ | _ | _ | _ | Injecting each disruption type mid-run visibly changes at least one in-flight proposal or reservation | T-9.1, T-5.3 |

### WP-10 — Report & Visualization  ·  requirements FR-MAP-01 (plus PROJECT.md Report generation)  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-10.1 | Markdown report template + fill-in script | - | _ | _ | _ | _ | Running it against one completed scenario_run produces a report with all five required sections | T-9.2 |
| T-10.2 | Post-run static image (Matplotlib + synthetic location graph) | FR-MAP-01 | _ | _ | _ | _ | One completed run produces one saved image file showing the final zone/unit state | T-9.1 |

### WP-11 — Testing  ·  requirements FR-RES-03, FR-SIM-01 (plus PROJECT.md's 4-layer test pyramid)  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-11.1 | Unit tests on core negotiation logic | - | _ | _ | _ | _ | The test suite covers every tiebreak branch and passes in CI | T-5.3 |
| T-11.2 | Scenario-replay regression test on one fixed scenario | FR-SIM-01 | _ | _ | _ | _ | Running the same scenario twice produces byte-identical scoring output | T-9.2 |
| T-11.3 | Property/fuzz test: a resource is never double-booked | FR-RES-03 | _ | _ | _ | _ | A randomized-input fuzz run of 1,000 proposal attempts never produces two live reservations on one unit | T-5.1 |
| T-11.4 | Structural check on Scenario Reader output | FR-SIM-01 | _ | _ | _ | _ | Feeding 10 malformed scenario texts to the checker correctly rejects all 10 before they reach the simulation | T-3.4 |

### WP-12 — Docs, CI & Demo Prep  ·  requirements NFR-MNT-01, NFR-SEC-04  ·  owner: me

| Task | Name | Reqs | O | M | P | E | Done when | Depends on |
|---|---|---|---:|---:|---:|---:|---|---|
| T-12.1 | README clean-machine test | NFR-MNT-01 | _ | _ | _ | _ | A clean clone reaches a running app in under 5 minutes using only the README | T-1.1,T-2.1a,T-2.1b,T-3.1,T-4.1,T-5.1,T-6.1,T-7.1,T-8.1,T-9.1,T-10.1,T-11.1 |
| T-12.2 | Automate the secret scan in CI | NFR-SEC-04 | _ | _ | _ | _ | A CI run on a commit containing a fake API key fails the build | — |
| T-12.3 | Author 3-5 pre-written demo scenarios | - | _ | _ | _ | _ | Each scenario file passes the structural check and produces a non-empty run | T-11.4 |
| T-12.4 | Record the post-run visualization into a short demo clip | - | _ | _ | _ | _ | One scenario's run produces a viewable short clip with no live network dependency at playback time | T-10.2 |

`E = (O + 4M + P) / 6`  ·  spread `P / O` over 4 means: spike it or split it.

## 4. Roll-up

*Pending — fill in once every task above has real O/M/P. Run `tools/plan-check.py docs/wbs.csv` and paste its REMAINING WORK table here, or compute by hand.*

| Work package | Tasks | Raw E (h) | Calibrated (h) |
|---|---:|---:|---:|
| WP-1 … WP-12 | 38 | `_` | `_` |
| **Total** | **38** | **`_`** | **`_`** |

Calibration factor from `docs/hours-log.csv`: **`_`×** (actual ÷ expected over tasks already finished; sample size: `_` tasks)

## 5. Schedule

*Pending — depends on §4's calibrated total and §2's real capacity numbers.*

| Week | Work packages in flight | Planned hours | Gate / dependency |
|---|---|---:|---|
| 9 | | | |

Rules: risky work first (WP-1, WP-2, WP-5 — the three things nobody's touched yet, per the risk register), integration before Week 12, nothing new starts after Week 14.

## 6. Burn-down baseline

*Pending — run `tools/plan-check.py docs/wbs.csv --buffer <your buffer>` once §3 and §4 are real; its BURN-DOWN table goes here.*

First week the plan exceeds remaining capacity: **`_`**
Hours over plannable: **`_`**

## 7. The scope decision

*Pending — depends on §6's gap, if any. Candidates already flagged in the risk register (R-05): WP-8 (notifications), WP-10's image/video polish, WP-9's disruption injectors (T-9.3) — lowest MoSCoW priority of the 12 work packages, touch none of the Must-priority negotiation/audit core.*

| Cut / deferred / re-estimated | Item | Reqs | Hours recovered | MoSCoW before → after | Why |
|---|---|---|---:|---|---|
| | | | `_` | | |

Signed: `_`, `_`. Re-baselined after any change of more than 5 hours.
