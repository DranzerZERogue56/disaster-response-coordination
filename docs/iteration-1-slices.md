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
| Commit | see git log ("Slice 2") |
| Not done | Marking the unit `assigned` on approval (slice 3, FR-RES-01). No background timer: expired reservations are freed the next time anything asks to reserve, not at the exact minute. A rejected proposal does not yet call `release_unit` (no rejection path exists until slices 3-4). Severity tiebreak (Milestone 12) |
| Ben's confidence | ____ / 100, colour: ____ |
