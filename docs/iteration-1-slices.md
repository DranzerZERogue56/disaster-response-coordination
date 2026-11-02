# Iteration 1 slice log (Milestone 10)

One section per slice, written when the slice lands. Evidence, not claims.
"Confidence" is Ben's own rating after he has looked at the slice: a number
0-100 and a colour (Green = I can explain every line and I watched it work;
Amber = it works but I have gaps; Red = I don't trust it yet).

Model note: all slices run on the rules-based fake model until Ollama is
wired in. Switching is one setting (`CLASSIFY_MODEL`), no code changes.

## Slice 1: Classify & Propose

| Item | Evidence |
|---|---|
| Requirements | FR-AGENT-01 (severity within 5 s, escalate if not confident), FR-AGENT-02 (proposal with unit, confidence, reasoning, alternatives) |
| Where it lives | `src/classify_propose/model.py` (swappable model, `FakeModel`), `src/classify_propose/service.py` (`classify_and_propose`), hook in `src/web_ui/app.py` (`POST /reports`) |
| Acceptance criteria | AC-1 a created report gets a severity and a proposal with all four parts. AC-2 a model answer that fails validation is never trusted: the report stays `created` for a human. AC-3 with no free unit it still proposes the best remaining one (out-of-service units are excluded) |
| Tests | `tests/test_classify_propose.py`: clear report, vague report (confidence 40, under 75), out-of-service unit skipped, invalid model output, no unit of needed type, unknown report. 9 of 9 pass locally with the intake tests |
| Handled failure path | `ClassifyError` codes `MODEL_OUTPUT_INVALID`, `NO_UNIT_OF_TYPE`, `REPORT_NOT_FOUND`; the route returns `needs_human` instead of a proposal |
| Seed data | `seed/iteration-1.sql` (one run, one Medical node, two Medical units) |
| Commit | `bd53194` |
| Not done | Reserving the unit (slice 2). Deciding or escalating by confidence (slices 3-4). Real model (Ollama main, Python-side fallback). The 5 s timing is not measured yet (fake model is instant) |
| Ben's confidence | 90 / 100, Green, 2026-11-01. Rated after opening `service.py` and the tests; the AI-usage entry should say so |

## Slice 2: Unit Registry reserve()

| Item | Evidence |
|---|---|
| Requirements | FR-RES-03 (unit reserved the moment it is proposed, reservation timestamped), NFR-REL-02 (reserved unit returns to available within 4 min). FR-COORD-01's second criterion (losing proposal finds the next best unit) is covered by the retry; the severity tiebreak is not |
| Where it lives | `src/unit_registry/service.py` (`reserve`, `reserve_for_proposal`, `release_expired`, `release_unit`), called from `POST /reports` in `src/web_ui/app.py` right after the proposal is written. Deliberately its own module, not inside Classify & Propose, so a break here is easy to isolate |
| Acceptance criteria | AC-1 proposing a unit reserves it, with `reserved_at` and a 4-minute `released_expected_by`. AC-2 reserving an already-reserved unit raises `UNIT_ALREADY_RESERVED` and leaves the first claim untouched. AC-3 when the recommended unit is taken, each alternative is tried in order and the proposal is updated to the one that won. AC-4 a reservation older than 4 minutes is freed |
| Tests | `tests/test_unit_registry.py`, 10 tests: reserve window, already reserved, out of service, missing unit, fallback to alternative, all taken (lists what was tried), frees at exactly 4:00 and not at 3:59, reserve again after expiry, immediate release, and an end-to-end route test (A gets unit 1, C gets unit 2, a third report gets 409). 19 of 19 pass locally |
| Handled failure path | `RegistryError`: `UNIT_ALREADY_RESERVED`, `UNIT_UNAVAILABLE`, `UNIT_NOT_FOUND`, `PROPOSAL_NOT_FOUND`. The route returns HTTP 409 with the units it tried when none can be reserved; the report and proposal rows stay in place |
| Commit | `fdee37b` |
| Not done | Marking the unit `assigned` on approval (slice 3, FR-RES-01). No background timer: expired reservations are freed the next time anything asks to reserve, not at the exact minute. A rejected proposal does not yet call `release_unit` (no rejection path exists until slices 3-4). Severity tiebreak (Milestone 12) |
| Ben's confidence | 95 / 100, Green, 2026-11-01. Rated after opening `src/unit_registry/service.py` |

## Slice 3: Decide Proposal auto-path

| Item | Evidence |
|---|---|
| Requirements | FR-AGENT-03 (auto only at confidence 75 or more and not high severity), NFR-SEC-02 (no dispatch without a human below 75 or at Severe/Critical), FR-RES-01 (approved proposal turns the reserved unit into an assigned one) |
| Where it lives | `src/decide_proposal/service.py` (`needs_human`, `decide_auto`), `src/unit_registry/service.py::assign_unit`, called from `POST /reports` after the reservation. Own module, like slice 2. Decide Proposal never writes to the units table; the registry does |
| Acceptance criteria | AC-1 confidence 75+ and not Severe/Critical: `final_status='approved'`, `decided_by='auto'`, `decided_at` set, unit goes `reserved` to `assigned`. AC-2 anything else is left untouched (no decision, unit stays reserved) for a human. AC-3 a second call returns the existing decision unchanged. AC-4 if the reservation was lost, `UNIT_NO_LONGER_AVAILABLE` is raised and the proposal stays undecided |
| Tests | `tests/test_decide_proposal.py`: the safety rule table (74 Moderate held; 75 and 90 Moderate auto; 95 Severe and 95 Critical held, plus 0, 100 and 100-Severe edges), the same five cases end to end against the database, idempotent second call, lost reservation, assign refuses another proposal's reservation, unknown proposal. Route test now checks A is auto-approved and C (Severe) is held. All pass locally |
| Handled failure path | `UNIT_NO_LONGER_AVAILABLE` (route returns 409). Held proposals are not errors |
| Commit | `353b437` |
| Not done | The human decision itself (slice 4). The real FR-RES-01 follow-up when the unit is lost (secondary path to a responder) is just the error for now. Batch-mode stand-in policy (60 threshold) is not built |
| Ben's confidence | 94 / 100, Green, 2026-11-01 |

## Slice 4: Decide Proposal escalation (human decision)

Spec: `.plans/slice-4-human-decision-spec.md`.

| Item | Evidence |
|---|---|
| Requirements | FR-AGENT-03 and NFR-SEC-02 (nothing is dispatched until a person decides, for held proposals) |
| Where it lives | `src/decide_proposal/service.py` (`decide_human`, `list_pending`, `stub_dispatcher_id`), `src/unit_registry/service.py::release_for_proposal`, routes `GET /proposals/pending` and `POST /proposals/<id>/decision` in `src/web_ui/app.py`, stand-in account in `seed/iteration-1.sql` |
| Acceptance criteria | AC-1 a held proposal is listed as pending, a decided one is not. AC-2 approve gives `approved`, `decided_by` is the dispatcher id (not `auto`), unit becomes `assigned`. AC-3 reject gives `rejected`, unit freed, report stays `classified`, no new proposal. AC-4 a second decision changes nothing. AC-5 approving after the reservation expired fails with `UNIT_NO_LONGER_AVAILABLE`, still undecided. AC-6 an observer account is refused |
| Tests | `tests/test_human_decision.py`, 12 tests, including reject not freeing another proposal's unit and the full demo beat through the HTTP routes (vague report held, listed as pending, approved by the stand-in dispatcher). 48 of 48 pass locally |
| Handled failure path | `UNIT_NO_LONGER_AVAILABLE` (409), `PROPOSAL_NOT_FOUND` (404), `INVALID_DECISION` (400), `NOT_A_DISPATCHER` (403), `STUB_DISPATCHER_MISSING` (500) |
| Commit | `17c66b0` |
| Not done | Real login (FR-AUTH-01), modify and override with a reason (FR-RES-02), automatic re-proposal after reject, a browser UI, the 45 s decision target (NFR-USE-01). The caller cannot name the dispatcher; the route always uses the seeded stand-in |
| Ben's confidence | 95 / 100, Green, 2026-11-01 |

## Slice 5: Notify Responder

| Item | Evidence |
|---|---|
| Requirements | FR-ALERT-01 (tell the assigned unit once the assignment is final). Gap in the requirement itself: the "within [X] seconds" number and both acceptance criteria are still `TODO` in `docs/requirements.md`, so this slice is built to the architecture contract (`docs/architecture.md`, Notify Responder) and the gap needs a change request |
| Where it lives | `src/notify_responder/service.py` (`notify_responder`, `notify_for_decision`), called from both approval paths in `src/web_ui/app.py` (auto-approve in `POST /reports`, human approve in `POST /proposals/<id>/decision`) |
| What "notify" means here | A row in `notifications` with `sent_at` set and `acknowledged_at` empty. No message leaves the machine; the requirement names no channel (architecture open question OQ-2). A real channel would replace one INSERT |
| Acceptance criteria | AC-1 an approved, assigned proposal gets a notification row with `sent_at`. AC-2 nothing is sent for a unit that is only reserved, for a held or rejected proposal, or for a unit assigned to a different proposal (`NOT_ASSIGNED`). AC-3 notifying the same assignment twice makes two rows (architecture contract). AC-4 a repeated approval call does not notify again. AC-5 a failed notification never undoes the approval; it is reported beside it |
| Tests | `tests/test_notify_responder.py`, 6 tests including the route-level beat: A auto-approved is notified at once, B held is not, B notified only after the dispatcher approves. 54 of 54 pass locally |
| Handled failure path | `NOT_ASSIGNED` (reported in the response as `notification.error`, decision stands) |
| Commit | `4955704` |
| Not done | A real delivery channel, acknowledgment tracking (FR-ALERT-02), the `UNIT_UNREACHABLE` error (needs a channel to be unreachable), the "within X seconds" target (X is undefined) |
| Ben's confidence | 95 / 100, Green, 2026-11-01 |

## Follow-up fixes after the self-review (2026-11-01 evening)

Ben's answers to the four findings that matter most (self-review 2.2, 3.2, 3.3, 4.1):

| Finding | What changed | Evidence |
|---|---|---|
| 2.2 no clock | A real clock: sweeper thread frees expired reservations every 5 s; `GET /units` and the `/reports` page show when each reserved unit will be freed and the seconds left | `tests/test_clock_and_atomicity.py`: clock numbers (240, 140, freed at 4:00), sweeper frees a stale reservation with nobody asking, route and page show it |
| 3.2 two saves | Assign and approve are one transaction on all three paths; on any failure both are undone | Tests force the decision save to fail and check the unit is still `reserved`; an invariant check ("assigned implies approved") after every normal path |
| 3.3 lost unit | Error code `UNIT_LOST_BEFORE_APPROVAL`, one automatic re-reserve and retry, reservation still shown | Tests: lost once is fixed and approved (`retried_after_unit_loss`); lost twice gives 409 with the new code, nothing assigned, nothing notified |
| 4.1 no login | Accepted; spoken line added to the demo script | `docs/demo/iteration-1-script.md`, 2:50 beat |

64 of 64 tests pass locally.

## Database-level rule (CR-001, migration 0002)

Ben's request after finding 3.2: "if it's assigned it's approved", enforced by the database itself.

| Item | Evidence |
|---|---|
| Requirements | FR-AGENT-03, NFR-SEC-02, FR-RES-01 (strengthened) |
| Where it lives | `migrations/0002-assigned-requires-approved.sql` (three triggers), `docs/change-requests/CR-001-assigned-requires-approved.md`, `CHANGELOG.md`, invariant I-assigned in `docs/architecture.md` |
| Rule | A unit cannot be inserted or updated to `assigned` unless its proposal is `approved` or `modified`; an approved proposal cannot be un-approved while a unit is assigned to it |
| Tests | `tests/test_database_rule.py` (9): direct SQL against undecided, rejected and escalated proposals is refused, approved and modified allowed, insert path refused, un-approving refused until the unit is freed, `tools/migrate.py` installs the triggers. Every other test now loads all migrations, so the whole suite runs with the triggers on |
| Not done | Reservations (`reserved` state) are still guarded by application code only |
| Ben's confidence | 95 / 100, Green, 2026-11-01 |

## Slice 6: Offline queue (Medium tier, extra slice 1)

| Item | Evidence |
|---|---|
| Requirements | FR-INTAKE-01 (queue while offline, drain in timestamp order), NFR-REL-03 (10 reports during an outage, 0 lost), FR-INTAKE-02 still applies offline |
| Where it lives | `src/intake_gateway/queue.py` (switch, `queued_report_ids`, `release_queued`, `drain_queue`), `queued` option in `src/intake_gateway/service.py::submit_report`, `process_report`/`drain_one` and `/connectivity` routes in `src/web_ui/app.py` |
| Acceptance criteria | AC-1 offline: a valid report is saved as `queued` (202), nothing else happens. AC-2 a malformed report is still rejected (400), not queued. AC-3 reconnecting processes queued reports oldest-first by reported time. AC-4 10 offline reports, 0 lost. AC-5 running out of units while draining loses nothing and does not stop the rest. AC-6 draining twice never processes a report twice |
| Tests | `tests/test_offline_queue.py` (8). 94 of 94 pass locally |
| Handled failure path | A drained report with no free unit reports `UNIT_ALREADY_RESERVED` in the reconnection response and stays `created`; invalid connectivity flag returns `INVALID_FLAG` (400) |
| Commit | `65d343b` |
| Not done | A maximum queue size (spec open question OQ-1). The switch is in memory, so it resets to connected on restart (the queue itself is in the database and survives). Timestamps are ordered as text, so mixed time zones could mis-order (self-review 6.4) |
| Ben's confidence | 85 / 100, Green, 2026-11-01 |

## Slice 7: Override Assignment (Medium tier, extra slice 2)

| Item | Evidence |
|---|---|
| Requirements | FR-RES-02 (override any assignment, only with a reason, logged with who/when/why/original choice/elapsed time, follow-up window), FR-AUDIT-02 |
| Where it lives | `src/override_assignment/service.py` (`override_assignment`, `add_follow_up`), `reassign` in `src/unit_registry/service.py`, routes `POST /assignments/<id>/override` and `POST /overrides/<id>/follow-up` in `src/web_ui/app.py`, table `dispatcher_overrides` (already in the schema) |
| Acceptance criteria | AC-1 an override with a reason moves the assignment and logs dispatcher, time, reason, the agent's original choice and (for a human-decided proposal) the seconds from AI escalation to human approval. AC-2 no reason is refused and nothing changes. AC-3 the follow-up is added to the same log entry, any time later, without touching the assignment. AC-4 a taken unit, an undecided proposal or an unknown id fail cleanly with no log row. AC-5 every override is its own row, even to the same unit. AC-6 an observer account is refused |
| Tests | `tests/test_override_assignment.py` (13), including the full path through the HTTP routes. 94 of 94 pass locally |
| Handled failure path | `REASON_REQUIRED` (400), `ASSIGNMENT_NOT_FOUND` (404), `NOT_A_DISPATCHER` (403), `UNIT_ALREADY_RESERVED` (409), `OVERRIDE_NOT_FOUND` (404), `FOLLOW_UP_REQUIRED` (400) |
| Commit | `a16e311` |
| Not done | Logging an observer's blocked attempt (needs real login, FR-AUTH-01). The log is not append-only yet (T-6.1), because the follow-up edits the same row as the spec asks. No warning when the new unit is a different type |
| Ben's confidence | 90 / 100, Green, 2026-11-01 |

## Self-review round 2 fixes (Ben's answers, 2026-11-01 evening)

| Finding | What changed | Evidence |
|---|---|---|
| 2.3 held proposal expiring | A held proposal whose unit's clock runs out times out (`rejected` / `timeout`), leaves the pending list, and a late approval changes nothing | `tests/test_human_decision.py` (3 tests replace the old "fails and stays undecided" one) |
| 2.4 concurrency | Real threads | `tests/test_timestamps_and_concurrency.py`: 8 threads, 1 winner |
| 6.4 timestamp order | Reported time stored as UTC; `INVALID_TIMESTAMP` for non-ISO input | Same file: five offset cases, bad inputs, and a mixed-time-zone queue drain |
| 7.2 append-only log | `override_follow_ups` table plus no-edit triggers (migration 0003, CR-002) | `tests/test_override_assignment.py`: edits to an override or a follow-up are refused |
| 1.3 / 1.5 measurement (Medium tier NFR) | `python -m src.classify_propose.measure --write` runs NFR-PERF-01's method and records the confidence spread | `docs/measurements.md`, `tests/test_measure.py`. Fake model only; the requirement is not met until run with the real model |

113 of 113 tests pass locally.

| Ben's confidence | 90 / 100, Green, 2026-11-01 |

## Demo fallback record

`python tools/demo_run.py` follows the demo script against the real app on a freshly seeded database and writes `docs/demo/iteration-1-run-transcript.md`: Report A auto-approved and notified, the visible reservation clock, Report B held and approved by the stand-in dispatcher (with the "no login yet" statement), Report C refused with HTTP 409, and the test suite (113 passed). It is a real run, not a mock-up, and is the fallback if the live recording goes wrong. The narrated screen recording is separate and is made by Ben.

