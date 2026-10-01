# Technical Specification — Disaster Response Coordination

Version: v0.1   Date: 2026-09-30   Author: Dranzer Rogue   Status: Draft
Requirements baseline this design satisfies: `docs/requirements.md` v1.2

## 1. Purpose and Scope

This document is the blueprint for the system described in `docs/requirements.md`: a tool that takes a disaster scenario, works out which responder types it needs, runs several candidate team sizes against a simulated version of that scenario with agents negotiating assignments in plain language, and writes up whichever team size performed best as a response plan a dispatcher could keep on file. It runs in two modes that share the same simulation and negotiation core: **batch mode**, which runs the team-size competition unattended (used for the graded evaluation runs in `PROJECT.md`'s Roster Competition), and **interactive mode**, a single live, slowed-down playback used for the capstone defense demo, where a real human dispatcher reviews and can override the agents' decisions through a web UI. The two modes exist because of a real conflict between two already-written documents: `PROJECT.md` calls for 5-10 unattended runs per team size (no human could plausibly sit through all of them), while `docs/requirements.md`'s FR-AGENT-03 requires a human to approve any low-confidence or high-severity proposal. Batch mode resolves this with a documented, logged stand-in auto-decide policy instead of a real human (see §5, Approval Gateway interface, and the Dependency Specification in §9 for why this is not "pretending a human approved it").

**In scope** (every requirement identifier below is satisfied by this design; see §10 for the full trace):
FR-INTAKE-01, FR-INTAKE-02, FR-INTAKE-03, FR-AGENT-01, FR-AGENT-02, FR-AGENT-03, FR-AGENT-04, FR-COORD-01, FR-COORD-02, FR-COORD-03, FR-RES-01, FR-RES-02, FR-RES-03, FR-DEGRADE-01, FR-DEGRADE-02, FR-DEGRADE-03, FR-DEGRADE-04, FR-INFER-01, FR-INFER-02, FR-INFER-03, FR-INFER-04, FR-ALERT-01, FR-ALERT-02, FR-MAP-01, FR-AUDIT-01, FR-AUDIT-02, FR-AUTH-01, FR-SIM-01, NFR-PERF-01, NFR-REL-01, NFR-REL-02, NFR-REL-03, NFR-REL-04, NFR-SEC-01, NFR-SEC-02, NFR-SEC-03, NFR-SEC-04, NFR-PRIV-01, NFR-ACC-01, NFR-ACC-02, NFR-USE-01, NFR-MNT-01.

**Out of scope, this design** (both are Could-priority in `docs/requirements.md` and are not built this release):
- **FR-COORD-04** (cross-agent consensus timeout) — the negotiation coordinator in §5 does not implement a 5-minute consensus fallback in v0.1; every scenario in this design's scope is small enough (a handful of team members per run) that a real consensus-timeout case has not been observed. Revisit if a walking-skeleton run (Week 9) actually stalls without one.
- **FR-MAP-02** (unit position tracking) — no live location feed exists or is planned (see ADR 0004, synthetic location graph); the dashboard shows zone boundaries (FR-MAP-01) but not moving units.
- **NFR-PORT-01** (portability) — already marked out of scope in `docs/requirements.md` §6.8; restated here because every requirement identifier in the baseline is required to appear in this document (`tools/spec-check.py`'s traceability check). This design is local-only, tied to one GPU host, and does not target multiple browsers or operating systems.

## 2. System Context (Level 1)

Diagram: [`docs/diagrams/context.dot`](diagrams/context.dot) + [`context.png`](diagrams/context.png)

| External actor / system | What it does with us | Protocol | If it is unavailable |
|---|---|---|---|
| Operator / student | Launches a batch competition run or the interactive demo | CLI (local process invocation) | Nothing runs; no degraded mode needed, this is the thing starting the system |
| Dispatcher (human) | Reviews and approves, modifies, rejects, or overrides an escalated proposal — interactive mode only | HTTP over localhost (the Web UI) | Interactive mode cannot proceed past an escalated proposal; batch mode is unaffected since it never needs a real human (see §5 Approval Gateway) |
| Scripted / typed scenario | Supplies incident reports — either a prewritten scripted sequence (FR-SIM-01) or plain-English text typed live for a demo | Intake API (FR-INTAKE-01), in-process for the scripted case | No reports arrive; the run produces nothing, logged as an empty run rather than a crash |
| Ollama (local LLM runtime) | Serves every classification, proposal-generation, and scenario-parsing call for the model `llama3.2:3b` | Local process call (Ollama's own local API, not a network host) | LLM Client's fallback chain engages: smaller local model, then a rules-based workflow, then a manual workflow (FR-DEGRADE-02) |

**Not shown, deliberately:** OSMnx / the Overpass API. ADR 0004 deferred real-street routing to a synthetic location graph for the MVP, so there is no live network call anywhere in the system boundary above — this is itself one of the facts NFR-SEC-01's connection-log test verifies.

## 3. Containers (Level 2)

Diagram: [`docs/diagrams/containers.dot`](diagrams/containers.dot) + [`containers.png`](diagrams/containers.png)

| Container | Responsibility (one sentence) | Technology | Runs where | Holds secrets? |
|---|---|---|---|---|
| Simulation & Negotiation Engine | Runs the multi-agent contract-net negotiation and the scripted/typed scenario playback, in both batch-scoring mode and interactive demo mode | Python 3.x, Mesa 3.5.1 (ADR 0003) | Operator's own machine, one process | No |
| Dispatcher Web UI | Serves the interactive-mode approve/modify/reject/override console to a human dispatcher | Python, Flask + plain HTML/JS, localhost only | Operator's own machine, interactive mode only | No (holds a session, not a secret key) |
| SQLite database | Stores every persisted entity — reports, proposals, audit trail, overrides, unit status, accounts — in one file | SQLite (public domain, ADR 0002) | Operator's own machine, one file, owner-only permissions | The single admin account's password hash (not a network secret) |
| Ollama | Loads and serves `llama3.2:3b` for every reasoning call | Ollama (MIT), model `llama3.2:3b` (ADR 0001) | Operator's own machine, separate local process | No |

**Trust boundary:** every container above runs on the operator's own machine. Nothing crosses out to a hosted or cloud service in the shipped MVP (FR-INFER-01, NFR-SEC-01, CON-03) — there is no API key anywhere in this system. The dispatcher's browser talks to the Web UI over `localhost` only; the Web UI and the Engine talk to each other over `localhost` only; nothing here is exposed to a real network interface.

## 4. Components (Level 3 — Simulation & Negotiation Engine)

Diagram: [`docs/diagrams/engine-components.dot`](diagrams/engine-components.dot) + [`engine-components.png`](diagrams/engine-components.png)

Chosen because this is the container where the hard part lives: the negotiation protocol, the confidence-threshold branch between batch and interactive mode, and the tiebreak logic.

| Component | Responsibility (verb first) | Owns (state) | Depends on | Serves (req IDs) |
|---|---|---|---|---|
| Scenario Reader | Translates a scripted or typed plain-English scenario into structured simulation settings | Nothing persisted (transient parse, held for the run) | LLM Client | FR-SIM-01 |
| Intake Gateway | Validates and queues incoming incident reports, rejects malformed ones, flags likely duplicates | The local offline queue (buffer awaiting reconnection) | Resource Agents | FR-INTAKE-01, FR-INTAKE-02, FR-INTAKE-03 |
| Resource Agents (Medical / Fire / Shelter / Security) | Classifies a report's severity and generates a proposed assignment with a confidence score and reasoning | Nothing persisted directly (writes through Audit Logger) | LLM Client, Negotiation Coordinator, Resource/Unit Registry | FR-AGENT-01, FR-AGENT-02, FR-AGENT-04 |
| Incident-Command Role | Sets the active run's negotiation ground rules; supplies the plain-language rationale the final report is built from | The run's ground-rules/policy (transient, run-scoped) | LLM Client, Negotiation Coordinator | Supports FR-COORD and report generation (PROJECT.md architecture; not itself a numbered requirement) |
| Negotiation Coordinator | Resolves conflicting proposals via announce-bid-award and the severity/richness/reported-first tiebreak | In-flight proposal/conflict state, consensus timers (transient, run-scoped) | Resource/Unit Registry, Audit Logger, Approval Gateway | FR-COORD-01, FR-COORD-02, FR-COORD-03 |
| Approval Gateway | Decides, per proposal, whether it auto-proceeds, gets the batch-mode stand-in policy, or escalates to a real human | The stand-in auto-decide policy configuration | Audit Logger; Dispatcher Web UI (interactive mode, cross-container) | FR-AGENT-03, NFR-SEC-02 |
| Resource/Unit Registry | Tracks every unit's availability and reservation state, and every agent node's heartbeat/liveness | The units table (status, reservation timestamps, node heartbeat) | Audit Logger, Notification Dispatcher | FR-RES-01, FR-RES-03, FR-DEGRADE-01 |
| Audit Logger | Logs every proposal (with the data used and confidence score) at generation time, and every dispatcher override, append-only | The audit_log and override_log tables | — (leaf) | FR-AUDIT-01, FR-AUDIT-02, FR-INFER-04, FR-AUTH-01 (the append-only log itself) |
| Notification Dispatcher | Notifies assigned responders and tracks acknowledgment | The notifications table | Audit Logger | FR-ALERT-01, FR-ALERT-02 |
| Roster Competition Runner | Orchestrates repeated batch runs across candidate team sizes and scenarios, scores each run | The scenario_runs/scores table | Scenario Reader, Resource Agents, Report & Visualization Generator | PROJECT.md's Roster Competition + Evaluation sections; operationally serves FR-SIM-01 |
| Report & Visualization Generator | Reads a finished run's logs and renders the Markdown report plus a static post-run image | Nothing persisted (writes generated files to `reports/`) | Audit Logger (read), Resource/Unit Registry (read) | FR-MAP-01 (rendered, not live), PROJECT.md Report generation |
| LLM Client | Wraps every Ollama call behind one shared interface; enforces local-only, the model-load fallback chain, the hardware check, and records which model/version served each call | Nothing persisted directly (writes model-version facts through Audit Logger) | Ollama (separate container) | FR-INFER-01, FR-INFER-02, FR-INFER-03, FR-INFER-04, FR-DEGRADE-02 |

**Dependency graph is acyclic: yes.** Everything bottoms out at Audit Logger or LLM Client, neither of which calls back upward into any other component in this list. Approval Gateway's one cross-container edge (to the Dispatcher Web UI, interactive mode only) doesn't create a cycle either — the Web UI never calls back into Approval Gateway's internal state, it only submits a decision through the same interface a batch-mode stand-in decision would use (see §5).

**Every piece of state has exactly one owner: yes.** No two components above claim the same table or the same transient state; see the "Owns" column — each row is unique.

## 5. Interface Contracts

One block per interface serving a Must-priority requirement. Eight facts each. Interfaces 1, 3, and 4 are the Web UI's real HTTP surface (localhost only); the rest are internal Python call contracts between components in the same process — still specified with the same eight facts, since an internal boundary is still a contract a stranger has to be able to implement against.

### Submit Incident Report                         (serves FR-INTAKE-01, FR-INTAKE-02, FR-INTAKE-03)
Purpose      Accept one incident report — from a simulated field agent, or from the Scenario Reader's scripted playback — validate it, and create or queue it
Auth         None (intake is unauthenticated; FR-AUTH-01's role model governs dispatcher actions, not report intake)
Request      `location` string required; `severity_raw` string required (free text, classified later by Classify & Propose); `timestamp` ISO 8601 UTC required; `reporting_unit` string required; `description` string optional
Success      `{report_id: int, status: "created"|"queued", received_at: ISO 8601 UTC}`
Errors       `FIELD_MISSING` — every missing field listed together, not one at a time (FR-INTAKE-02); `FIELD_INVALID` — a present field fails its format rule (e.g. timestamp not ISO 8601), also listed together with any `FIELD_MISSING` hits in one response
Idempotency  Not idempotent by a caller-supplied ID. Two reports within 1 block and 10 minutes with a matching address or corroborating description are instead flagged a probable duplicate and merged for accuracy (FR-INTAKE-03), not rejected
Side effects Writes a row to `incident_reports` (or the offline queue, if the connectivity flag is down); on creation, triggers Classify & Propose for that report
Limits       The offline queue drains in timestamp order on reconnection, oldest first, so a reconnection burst can't overwhelm the system at once (FR-INTAKE-01); the queue has no fixed maximum size in this release — open question OQ-1 (§11)

### Classify & Propose                              (serves FR-AGENT-01, FR-AGENT-02, FR-AGENT-04)
Purpose      Classify a created report's severity and generate a resource-assignment proposal with a confidence score, reasoning, and alternatives
Auth         Internal call only; invoked by Intake Gateway on report creation
Request      `{report_id: int, report_fields: object}`
Success      `{severity: Minor|Moderate|Serious|Severe|Critical, confidence: int 0-100, recommended_unit_id: int, reasoning: string, alternatives: [unit_id]}`
Errors       `CLASSIFICATION_UNCERTAIN` — the model can't confidently pick a severity; escalates to a human directly instead of guessing (FR-AGENT-01); `REASONING_TIMEOUT` — exceeded the ~60s budget, falls back to a non-LLM path and reports to the human overseer (FR-AGENT-04)
Idempotency  Not idempotent — a repeat call for the same `report_id` produces a new, independently-reasoned proposal (the model isn't guaranteed deterministic), logged separately
Side effects Writes the proposal through Log Decision *before* any approval decision exists (FR-AUDIT-01); reserves the recommended unit through the Resource/Unit Registry at the moment the proposal is made (FR-RES-03)
Limits       One in-flight classification per `report_id`; a second concurrent call for the same report returns `ALREADY_IN_PROGRESS`

### Decide Proposal                                 (serves FR-AGENT-03, NFR-SEC-02)
Purpose      Resolve whether a proposal proceeds automatically, through the batch-mode stand-in policy, or through a real dispatcher's decision — one interface, two callers
Auth         Batch mode: none, internal call from Roster Competition Runner. Interactive mode: a dispatcher-role session (FR-AUTH-01); an observer-role session may view the pending queue but calling this interface's approve/modify/reject actions is blocked and logged
Request      `{proposal_id: int, decision: "approve"|"modify"|"reject", modified_unit_id: int (required if decision=modify), decided_by: "stand-in-policy"|dispatcher_account_id}`
Success      `{proposal_id: int, final_status: "approved"|"modified"|"rejected", decided_at: ISO 8601 UTC}`
Errors       `BELOW_THRESHOLD_NO_DECIDER` — confidence under 75 or severity Severe/Critical, and no decider is configured for this run (a configuration error, not a normal path); `UNIT_NO_LONGER_AVAILABLE` — the named unit was reserved by another proposal first, triggers FR-RES-01's secondary follow-up
Idempotency  A second call on an already-decided `proposal_id` returns the existing decision unchanged (`ALREADY_DECIDED`) rather than deciding twice
Side effects Proposals with confidence ≥ 75 **and** severity not Severe/Critical never reach this interface — they auto-proceed straight to Reserve Unit (NFR-SEC-02). Everything else routes here. In batch mode, the stand-in policy approves at confidence ≥ 60 and otherwise logs the proposal as `UNRESOLVED_WOULD_ESCALATE`, scored accordingly rather than blocking the run — a deliberate, disclosed approximation of a human, recorded in ADR 0006, never silently presented as a real approval. Every stand-in decision is logged with `decided_by: "stand-in-policy"` so it's never confused with a dispatcher's decision in the audit trail
Limits       Interactive mode targets a dispatcher decision within 45s of the proposal appearing in the Web UI (NFR-USE-01) — a usability target measured by observation, not a server-enforced timeout

### Override Assignment                             (serves FR-RES-02, FR-AUDIT-02)
Purpose      Let a dispatcher replace any system-generated assignment, at any time, with a reason
Auth         Dispatcher-role session required; an observer-role session is blocked and the attempt is logged (FR-AUTH-01)
Request      `{assignment_id: int, new_unit_id: int, reason: string (required, non-empty)}`
Success      `{assignment_id: int, override_id: int, status: "overridden", logged_at: ISO 8601 UTC}`
Errors       `REASON_REQUIRED` — rejected outright until a reason is supplied (FR-RES-02); `ASSIGNMENT_NOT_FOUND`
Idempotency  Not idempotent — every call creates a new `override_log` row, even repeating the same `new_unit_id`; each is its own decision worth its own record
Side effects Logs who, when, why, the original agent choice, and the elapsed time between AI escalation and human approval (FR-RES-02); takes effect immediately, then opens an unlimited follow-up window where the dispatcher may add to the same log entry without blocking the original decision
Limits       None specified; a dispatcher may override the same assignment any number of times

### Resource/Unit Registry                          (serves FR-RES-01, FR-RES-03, FR-DEGRADE-01)
Purpose      Track every unit's availability/reservation state, and detect a silent agent node
Operations   `reserve(unit_id, incident_id)`, `release(unit_id)`, `get_status(unit_id)`, `heartbeat(node_id)`
Auth         Internal call only
Request      `reserve`: `{unit_id: int, incident_id: int, reserved_by: proposal_id}`. `heartbeat`: `{node_id: string, timestamp: ISO 8601 UTC}`
Success      `reserve` → `{unit_id: int, status: "reserved", reserved_at: timestamp}`; `heartbeat` → `{node_id: string, status: "alive"}`
Errors       `UNIT_ALREADY_RESERVED` — another proposal reserved it first; the caller proposes the next-best available unit instead (FR-COORD-01); `NODE_NOT_RESPONDING` — raised by the registry's own poll, not the node, once 30s pass with no heartbeat (FR-DEGRADE-01)
Idempotency  `release` on an already-available unit is a no-op returning current state, not an error. `reserve` on an already-reserved unit always fails — this is the exact mechanism FR-RES-03 relies on to prevent double-booking
Side effects Every status change (reserve, release, node-down, node-recovered) is pushed to every other agent, and cached if delivery fails (FR-RES-03). A released reservation returns to available within 4 minutes (NFR-REL-02). A recovered node is marked recovered and requires a human to confirm the interruption didn't affect any information before its data is trusted again (FR-DEGRADE-01)
Limits       Heartbeat checked every 10s; 3 consecutive misses (30s) trips `NODE_NOT_RESPONDING`

### Resolve Negotiation Conflict                    (serves FR-COORD-01, FR-COORD-02, FR-COORD-03)
Purpose      Apply the one tiebreak rule — severity, then information richness, then reported-first — whenever two agent proposals can't both be satisfied
Auth         Internal call only
Request      `{proposal_a: proposal_id, proposal_b: proposal_id}`
Success      `{winner: proposal_id, loser: proposal_id, reason: "severity"|"richness"|"reported-first", resolved_at: timestamp}`
Errors       `TRUE_TIE` — identical across all three dimensions; both proposals are validated, one proceeds, the other is kept as history rather than discarded (FR-COORD-03)
Idempotency  Resolving the same pair twice returns the same winner deterministically — the tiebreak is a pure function of already-logged data that doesn't change afterward
Side effects The losing agent finds and proposes the next-best available unit (FR-COORD-01). If the conflict was two agents' different pictures of the same incident rather than a unit claim, the newer-timestamped data becomes the active record unless a human overrides it — logged the same way as an Override Assignment call (FR-COORD-02)
Limits       None specified

### Log Decision                                    (serves FR-AUDIT-01, FR-AUDIT-02, FR-INFER-04, FR-AUTH-01)
Purpose      Record every agent proposal and every dispatcher override, append-only — the log reflects what was actually reasoned and decided, never edited after the fact
Operations   `log_proposal(...)`, `log_override(...)`, `get_entries(filter)`
Auth         Internal `log_*` calls from any component; `get_entries` requires a dispatcher or admin session
Request      `log_proposal`: `{report_id, severity, confidence, recommended_unit_id, reasoning, model_identifier, model_version, generated_at}` — this is where FR-INFER-04's model-version pinning is recorded
Success      `{entry_id: int, logged_at: timestamp}`
Errors       `WRITE_FAILED` — always surfaced to the human overseer, never silently retried, since a missing audit entry defeats the explainability requirement this interface exists for
Idempotency  Every call creates a new row; there is no update or delete operation on this interface — only `put` (create) and `get` (read) exist, by design (FR-AUTH-01: "no one, including the admin, can delete entries")
Side effects None beyond the write itself
Limits       No cap on entry count inside the 24-hour retention window (NFR-PRIV-01); the scheduled purge job, not this interface, removes rows after 24 hours

### LLM Generate                                    (serves FR-INFER-01, FR-INFER-02, FR-DEGRADE-02)
Purpose      The one shared interface every reasoning call goes through — classification, proposal generation, scenario parsing — wrapping Ollama and the local-only guarantee. Full budget/fallback/verification detail is in §9; this entry is the calling contract only
Auth         Internal call only
Request      `{prompt: string, output_schema: JSON schema, caller: component name}`
Success      `{output: object validated against output_schema, model_identifier: "llama3.2:3b", latency_ms: int}`
Errors       `SCHEMA_VALIDATION_FAILED` — one retry with the schema restated in the prompt, then falls through to FR-DEGRADE-02's fallback chain; `TIMEOUT` — exceeded ~60s (FR-AGENT-04); `MODEL_UNAVAILABLE` — Ollama process unreachable
Idempotency  Not idempotent — model output is not guaranteed identical between calls; every call is its own reasoning attempt
Side effects Never makes an outbound call to any host outside the local machine, even if one is reachable — enforced in code, not just configuration (FR-INFER-01), and what NFR-SEC-01's connection-log test checks for
Limits       One concurrent call per caller; the ~60s timeout is per call, not cumulative

### Play Scenario                                   (serves FR-SIM-01)
Purpose      Replay a prewritten incident sequence at a controlled pace, on demand, so the same scenario runs reliably for a batch run or the capstone defense
Auth         Internal call, invoked by the Operator via CLI (batch mode) or the interactive-mode launcher
Request      `{scenario_file: path, pace: "scripted"|"live-typed", speed_multiplier: float}`
Success      `{run_id: int, reports_queued: int, started_at: timestamp}`
Errors       `SCENARIO_FILE_INVALID` — malformed scenario file, fails before any report reaches Submit Incident Report
Idempotency  Each call starts a new, independently-numbered run; replaying the same file twice yields two separate `run_id`s by design — exact repeatability is the point, not deduplication
Side effects Feeds every report in the sequence through Submit Incident Report at the scenario's defined pace
Limits       None specified

### Notify Responder                                (serves FR-ALERT-01)
Purpose      Notify the unit assigned to an incident once the assignment is finalized
Auth         Internal call only
Request      `{assignment_id: int, unit_id: int}`
Success      `{notification_id: int, sent_at: timestamp}`
Errors       `UNIT_UNREACHABLE` — no acknowledgment channel is configured for this unit in this release (open question OQ-2, §11 — FR-ALERT-01 doesn't specify the actual channel)
Idempotency  Re-notifying the same `assignment_id` creates a new notification row rather than suppressing the repeat — a dispatcher should be able to see a double notification if one happened
Side effects None beyond the notification record. Acknowledgment tracking (FR-ALERT-02, Should-priority) isn't implemented by this interface in v0.1; `notifications` reserves a nullable `acknowledged_at` column for it (§6)
Limits       None specified

Error envelope used system-wide:
```json
{
  "error": {
    "code": "ONE_OF_THE_CODES_NAMED_ABOVE",
    "message": "human-readable, specific to this call",
    "field": "set only for a per-field validation error, otherwise absent",
    "retryable": false
  }
}
```
Every error code named in the ten interfaces above fits this one shape; no interface invents its own error format.

Status-code policy (the Web UI's HTTP surface only — Submit Incident Report, Decide Proposal's interactive path, and Override Assignment; every other interface above is an internal Python call that raises an exception carrying the same `code` field, not an HTTP status):

| Code | Meaning in this system |
|---|---|
| 200 | Success |
| 400 | `FIELD_MISSING` / `FIELD_INVALID` / `REASON_REQUIRED` |
| 401 | No valid dispatcher session |
| 403 | Session valid but the role forbids this action (FR-AUTH-01) |
| 404 | Referenced report/proposal/assignment/unit does not exist |
| 409 | `UNIT_ALREADY_RESERVED`, or a conflicting concurrent decision |
| 422 | Well-formed request, semantically invalid (e.g. severity outside the five defined levels) |
| 500 | `WRITE_FAILED` or any unhandled internal error — the response body never includes report content (NFR-SEC-03); detail lives only in the audit log |
| 503 | `MODEL_UNAVAILABLE` after every fallback in FR-DEGRADE-02's chain is exhausted |

## 6. Data Model

Key decisions made before writing this section (confirmed by the author, not the assistant's default): an agent **node maps to one role-type** (Medical, Fire, Shelter, Security, plus Incident-Command — five nodes per run, not one per individual unit); **integer auto-increment primary keys** throughout; **plain numbered SQL migrations with a `schema_migrations` table**, forward-only; the admin password is hashed with **`hashlib.scrypt`** (Python stdlib, no new dependency), salted, never stored in the repository (NFR-SEC-04).

**One structural simplification worth stating explicitly:** there is no separate `assignments` table. An "assignment" (FR-RES-01) is an `agent_proposals` row whose `final_status` is `approved` or `modified` — the proposal and the assignment are the same row at two points in its life, not two entities that would otherwise have to be kept in sync.

**Timestamp convention, decided once:** every timestamp column is ISO 8601 UTC, generated at write time. Local time is computed exactly once, in the Dispatcher Web UI's rendering layer, for display only — never stored.

### Entity: incident_reports                        (serves FR-INTAKE-01, FR-INTAKE-02, FR-INTAKE-03)
Purpose        One row per incident report, whether it arrived validated or is still waiting in the offline queue
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| scenario_run_id | INTEGER | NOT NULL | FK scenario_runs.id — which run this report belongs to |
| location | TEXT | NOT NULL | Free-text location |
| severity_raw | TEXT | NOT NULL | The original free-text severity input, pre-classification |
| severity | TEXT | NULL | One of Minor/Moderate/Serious/Severe/Critical; NULL until Classify & Propose completes |
| timestamp_reported | TEXT | NOT NULL | ISO 8601 UTC, when the report was made |
| reporting_unit | TEXT | NOT NULL | Which simulated field unit reported it |
| description | TEXT | NULL | Optional free text |
| status | TEXT | NOT NULL | `queued` \| `created` \| `classified` \| `duplicate_merged` |
| duplicate_of_id | INTEGER | NULL | FK incident_reports.id; set only when status=`duplicate_merged` |
| received_at | TEXT | NOT NULL | ISO 8601 UTC, when the row was actually created (may be later than timestamp_reported if it was queued) |
Invariants     I1: `severity` is NULL only while status is `queued` or `created`. I2: `duplicate_of_id` is set only when status=`duplicate_merged`, and never points at a row that is itself `duplicate_merged` (merge directly to the original, no chains). I3: a `queued` row has zero `agent_proposals` referencing it — nothing reasons on unvalidated, undelivered data.
Relationships  One incident_report → many agent_proposals (0..N). One incident_report → 0 or 1 duplicate_of (self-referential). Many incident_reports → one scenario_run.
Volume         30-50 rows per run (`PROJECT.md`'s stated scenario scale) × an estimated 45-250 batch runs across the semester (3-5 team sizes × 3-5 scenarios × 5-10 repeats) = roughly 1,350-12,500 rows generated by Week 16 — not resident at once, since NFR-PRIV-01 purges each row 24h after `received_at`
Lifecycle      Created at intake (or `queued`, then `created` on reconnection); purged 24h after `received_at` (NFR-PRIV-01), regardless of whether the Report & Visualization Generator has already read it — see Open Question OQ-3 (§11)

### Entity: agent_proposals                         (serves FR-AGENT-01, FR-AGENT-02, FR-AGENT-03, FR-AUDIT-01, FR-INFER-04, FR-RES-01)
Purpose        One row per reasoning attempt; becomes the operative "assignment" once `final_status` is set to `approved` or `modified`
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| report_id | INTEGER | NOT NULL | FK incident_reports.id |
| agent_node_id | INTEGER | NOT NULL | FK agent_nodes.id — which role-type node generated this |
| confidence | INTEGER | NOT NULL | 0-100 |
| recommended_unit_id | INTEGER | NOT NULL | FK units.id |
| reasoning | TEXT | NOT NULL | The agent's plain-language rationale |
| alternatives | TEXT | NOT NULL | JSON array of unit_ids — read-only, never queried relationally, so a join table would add structure with no use |
| model_identifier | TEXT | NOT NULL | e.g. `llama3.2:3b` |
| model_version | TEXT | NOT NULL | Ollama's reported version/digest (FR-INFER-04) |
| decided_by | TEXT | NULL | NULL until decided; else `auto`, `stand-in-policy`, or a dispatcher_accounts.id (as text) |
| final_status | TEXT | NULL | NULL until decided; else `approved` \| `modified` \| `rejected` \| `unresolved_would_escalate` |
| generated_at | TEXT | NOT NULL | Logged before any decision exists (FR-AUDIT-01) |
| decided_at | TEXT | NULL | Set together with final_status and decided_by, atomically |
Invariants     I1: `decided_at` is NULL if and only if `final_status` is NULL. I2: once `final_status` is set, no column on this row ever changes again — the one update that sets `final_status`/`decided_by`/`decided_at` together is the last write this row ever receives. I3: `confidence ≥ 75` and severity not Severe/Critical implies `decided_by = 'auto'` (NFR-SEC-02).
Relationships  Many agent_proposals → one incident_report; many → one agent_node; many → one units (as recommended_unit_id).
Volume         Roughly 1-1.5× the incident_reports count (a minority get a second reasoning attempt after a timeout or uncertain classification) — an estimated 1,500-18,000 rows generated by Week 16, same 24h purge
Lifecycle      Created once at generation; exactly one later update sets the decision; purged 24h after `generated_at` with the rest of the audit trail (NFR-PRIV-01)

### Entity: dispatcher_overrides                    (serves FR-RES-02, FR-AUDIT-02, FR-COORD-02's override path)
Purpose        One row per dispatcher override of an assignment, at any point in its life
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| assignment_id | INTEGER | NOT NULL | FK agent_proposals.id — the proposal being overridden |
| dispatcher_account_id | INTEGER | NOT NULL | FK dispatcher_accounts.id |
| new_unit_id | INTEGER | NOT NULL | FK units.id |
| original_agent_choice_unit_id | INTEGER | NOT NULL | FK units.id — snapshot of what the agent had chosen, so it stays comparable even after further changes |
| reason | TEXT | NOT NULL | Required at submission time; rejected until non-empty |
| follow_up_explanation | TEXT | NULL | Added later, in the no-time-pressure window — the one documented exception to "never update a row" in this schema |
| ai_escalated_at | TEXT | NULL | When the AI requested human approval, if this override followed an escalation |
| overridden_at | TEXT | NOT NULL | |
Invariants     I1: `reason` is non-empty (app-layer check, not a bare NOT NULL, since an empty string would pass NOT NULL). I2: `ai_escalated_at ≤ overridden_at` whenever `ai_escalated_at` is not NULL.
Relationships  Many dispatcher_overrides → one agent_proposals; many → one dispatcher_accounts; many → one units (twice: new_unit_id and original_agent_choice_unit_id).
Volume         Expected minority of finalized proposals — estimated low hundreds across the semester's testing, same 24h purge
Lifecycle      Created once at override; `follow_up_explanation` may be added exactly once afterward; purged 24h with the rest of the audit trail

### Entity: units                                   (serves FR-RES-01, FR-RES-03)
Purpose        One row per responder unit that exists within one scenario run's team-size configuration — not a persistent real-world fleet, a simulated roster re-created per run
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| scenario_run_id | INTEGER | NOT NULL | FK scenario_runs.id |
| unit_type | TEXT | NOT NULL | `Medical` \| `Fire` \| `Shelter` \| `Security` |
| agent_node_id | INTEGER | NOT NULL | FK agent_nodes.id — the role-type node managing this unit |
| status | TEXT | NOT NULL | `available` \| `reserved` \| `assigned` \| `out_of_service` |
| reserved_by_proposal_id | INTEGER | NULL | FK agent_proposals.id; set when status is `reserved` or `assigned` |
| reserved_at | TEXT | NULL | |
| released_expected_by | TEXT | NULL | `reserved_at` + 4 minutes — what NFR-REL-02's test polls against |
Invariants     I1: `status = 'available'` implies `reserved_by_proposal_id IS NULL`. I2: `status IN ('reserved','assigned')` implies `reserved_by_proposal_id IS NOT NULL`. I3: at most one unit row may carry a given `reserved_by_proposal_id` — enforced by requiring `reserve()` to check `status='available'` and write the reservation in the same transaction, which is the actual mechanism FR-RES-03 depends on to prevent double-booking.
Relationships  Many units → one agent_node; many → one scenario_run; one unit → 0 or 1 agent_proposals (reserved_by, at a time).
Volume         25-40 rows per run (`PROJECT.md` scope) × 45-250 runs = roughly 1,125-10,000 rows generated by Week 16
Lifecycle      Created at run start (one row per unit in that run's configuration); status updated in place throughout the run (not append-only — this is current state, not an audit record); purged with the run's data 24h after the run's reports were received

### Entity: agent_nodes                              (serves FR-DEGRADE-01, FR-DEGRADE-02)
Purpose        One row per role-type agent process within one scenario run (Medical, Fire, Shelter, Security, Incident-Command — five per run)
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| scenario_run_id | INTEGER | NOT NULL | FK scenario_runs.id |
| role_type | TEXT | NOT NULL | `Medical` \| `Fire` \| `Shelter` \| `Security` \| `IncidentCommand` |
| status | TEXT | NOT NULL | `alive` \| `not_responding` \| `recovered` |
| last_heartbeat_at | TEXT | NOT NULL | |
| recovered_confirmed_by | INTEGER | NULL | FK dispatcher_accounts.id — FR-DEGRADE-01's required human confirmation that an interruption didn't affect any information |
Invariants     I1: `status = 'not_responding'` implies more than 30 seconds have passed since `last_heartbeat_at` (the detection threshold). I2: `status = 'recovered'` implies `recovered_confirmed_by IS NOT NULL` — a node cannot be fully trusted again without the human check.
Relationships  Many agent_nodes → one scenario_run; one agent_node → many units (the ones it manages); one agent_node → many agent_proposals (the ones it generated).
Volume         5 rows per run × 45-250 runs = roughly 225-1,250 rows by Week 16 — trivial
Lifecycle      Created at run start; `status`/`last_heartbeat_at` updated in place (current state, not an audit record); purged with the run's data at 24h

### Entity: dispatcher_accounts                     (serves FR-AUTH-01)
Purpose        One row per dispatcher/admin/observer account — all fictional test identities in this release
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| username | TEXT | NOT NULL | UNIQUE |
| password_hash | TEXT | NOT NULL | `hashlib.scrypt` output, hex-encoded |
| password_salt | TEXT | NOT NULL | Hex-encoded, generated with `os.urandom(16)` per account |
| role | TEXT | NOT NULL | `admin` \| `dispatcher` \| `observer` — MVP populates one `admin` plus a small number of fictional `dispatcher` test accounts |
| is_fictional_test_account | INTEGER | NOT NULL | Always 1 (true) in this release (NFR-SEC-03); the column exists so a real-deployment release has somewhere to flip it |
| created_at | TEXT | NOT NULL | |
Invariants     I1: exactly one row has `role = 'admin'` (the single-admin-account decision, `docs/requirements.md` §6.4.1). I2: `is_fictional_test_account` is always 1 in this release.
Relationships  One dispatcher_account → many dispatcher_overrides; one → many agent_proposals (where decided_by names this account).
Volume         Single digits; fixed, not scenario-scoped
Lifecycle      Created once at setup; **never auto-purged** — this is account data, not incident data (`docs/requirements.md` §6.4.1: "Life of the project"); deleted only by the admin, manually

### Entity: notifications                           (serves FR-ALERT-01, FR-ALERT-02)
Purpose        One row per responder notification sent for a finalized assignment
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| assignment_id | INTEGER | NOT NULL | FK agent_proposals.id |
| unit_id | INTEGER | NOT NULL | FK units.id |
| sent_at | TEXT | NOT NULL | |
| acknowledged_at | TEXT | NULL | Reserved for FR-ALERT-02 (Should-priority, not implemented in v0.1's logic — the column exists now so this isn't a schema migration later) |
Invariants     None beyond the two foreign keys.
Relationships  Many notifications → one agent_proposals; many → one units.
Volume         Roughly one per finalized assignment — same order of magnitude as `approved`/`modified` rows in agent_proposals
Lifecycle      Created once at notify time; purged with the run's data at 24h

### Entity: scenario_runs                           (serves FR-SIM-01; PROJECT.md's Roster Competition and Evaluation)
Purpose        One row per batch or interactive run — the one entity that deliberately outlives the 24h purge, since the whole point of the roster competition is comparing runs across the semester
| Column | Type | Null | Meaning |
|---|---|---|---|
| id | INTEGER | NOT NULL | Primary key |
| mode | TEXT | NOT NULL | `batch` \| `interactive` |
| scenario_file | TEXT | NOT NULL | Which scenario was played |
| team_size_config | TEXT | NOT NULL | JSON, e.g. `{"Medical":10,"Fire":8,"Shelter":5,"Security":7}` |
| started_at | TEXT | NOT NULL | |
| finished_at | TEXT | NULL | NULL while the run is in progress |
| score | REAL | NULL | The overall effectiveness score (`PROJECT.md` Evaluation); NULL until scoring completes |
| unresolved_would_escalate_count | INTEGER | NOT NULL | Default 0 — how many proposals hit the batch stand-in's unresolved path (ADR 0006's transparency requirement) |
Invariants     I1: `finished_at IS NOT NULL` implies `score IS NOT NULL` — a finished run is always scored before it's considered done.
Relationships  One scenario_run → many agent_nodes, many units, many incident_reports.
Volume         Up to roughly 250 rows across the whole semester (upper bound of 5 team sizes × 5 scenarios × 10 repeats) — trivial
Lifecycle      Created at run start; updated once at completion (score, finished_at, counts); **persists for the life of the project** — this is the one deliberate exception to the 24h purge, since the final written comparison in Week 16 needs every prior run's score, not just the raw incident data NFR-PRIV-01 is actually about

### Migrations
Mechanism      Plain numbered SQL files applied in order, tracked in a `schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)` table — no migration library, consistent with this project's existing low-dependency pattern (Jinja2-or-f-strings for the report generator, no ORM)
Direction      Forward-only. A 16-week solo project with one developer and no shared staging database has little use for rollback migrations; if a migration turns out wrong, the fix is a new, higher-numbered migration, not a reverse of the old one
Path + runner  `migrations/0001-initial.sql`, applied by `tools/migrate.py <db-path>` — the runner reads every `migrations/NNNN-*.sql` file whose number isn't already in `schema_migrations`, applies it inside one transaction, and records the version
Conventions    All timestamps stored as ISO 8601 UTC text (SQLite has no native timestamp type); all IDs are integer auto-increment; enums are plain TEXT constrained by the invariants above, not a SQL CHECK constraint (SQLite's CHECK support is usable but the project's existing checkers (`tools/check_requirements.py`-style scripts) are the established pattern for enforcing structure, so enum validation happens at the Python layer, consistent with that)
