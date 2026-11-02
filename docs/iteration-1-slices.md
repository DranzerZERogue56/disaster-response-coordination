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
| Commit | see git log ("Slice 4") |
| Not done | Real login (FR-AUTH-01), modify and override with a reason (FR-RES-02), automatic re-proposal after reject, a browser UI, the 45 s decision target (NFR-USE-01). The caller cannot name the dispatcher; the route always uses the seeded stand-in |
| Ben's confidence | ____ / 100, colour: ____ |
