# Iteration 1 self-review (Milestone 10)

**Status: DRAFT written by the AI assistant, 2026-11-01. Ben has not yet corrected it.** Every finding below must be checked by Ben against the code before this file counts as his review. Where he disagrees, he changes the disposition and says why.

**About the four passes:** the assignment asks for "the four passes" but the passes are not defined in the assignment text or the course's `10-iteration-one-building-the-core/code` folder that I could reach. This draft uses four common ones. If the textbook names different ones, rename the headings and re-sort the findings (open item for Ben).

1. **Correctness:** does the code do what the acceptance criteria say?
2. **Failure paths:** what happens when inputs, timing or neighbours go wrong?
3. **Safety and security:** can the safety rule or a boundary be bypassed?
4. **Readability and tests:** could a stranger follow it, and do the tests prove it?

Dispositions: **Fixed** (with commit), **Defect** (logged in `docs/review/review-defect-log.csv` style, with a target), **Accepted** (with a written reason).

## Slice 1: Classify & Propose (`src/classify_propose/`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 1.1 | Correctness | Classifying the same report twice would insert a second proposal for it (no check on report status) | **Fixed** this session: `ALREADY_CLASSIFIED` error plus `test_classifying_twice_does_not_make_a_second_proposal` |
| 1.2 | Failure paths | A model answer with a bad severity, unit type, confidence or empty reasoning is rejected and the report is left for a human | No change needed; covered by `test_invalid_model_output_leaves_report_for_a_human` |
| 1.3 | Correctness | The 5-second limit (FR-AGENT-01) is not measured; the fake model answers instantly | **Accepted** for now: only meaningful once a real model exists. Measuring is a Medium-tier item |
| 1.4 | Readability | `FakeModel` matches word fragments (for example "gun" would match "begun", "conscious" matches "unconscious"), so it can mislabel unusual wording | **Accepted**: it is a stand-in whose only job is to be predictable for tests and the demo; it will be replaced |
| 1.5 | Safety | The confidence number comes from the model itself, and a small model's self-reported confidence can be unreliable | **Accepted** with a plan: Ben chose to let the model report it and tune if Report B does not land under 75; the safety rule in slice 3 still holds Severe/Critical regardless |

## Slice 2: Unit Registry (`src/unit_registry/service.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 2.1 | Correctness | Reserving is one conditional UPDATE that only matches an available unit, so two requests cannot both win | No change needed; covered by `test_reserving_a_reserved_unit_raises_unit_already_reserved` (sequential only, see 2.4) |
| 2.2 | Failure paths | Expired reservations are freed only when someone next asks to reserve; there is no timer, so NFR-REL-02's "within 4 minutes" holds only while traffic arrives | **Fixed** (Ben: 'there should be a set clock anyone using the software can see'): a background sweeper frees expired reservations every 5 s (`SWEEP_SECONDS`, started by `script/start`), `unit_clock()` and `GET /units` show each unit's `frees_at` and `seconds_left`, and the `/reports` page shows the same table, refreshing every 5 s. Tests in `tests/test_clock_and_atomicity.py` |
| 2.3 | Failure paths | A proposal held for a human loses its unit after 4 minutes and still shows in `/proposals/pending`; approving it then fails with `UNIT_NO_LONGER_AVAILABLE` | **Defect**, target Milestone 11/12 (FR-AGENT-04 timeout handling: mark it, drop it from the pending list). The 4-minute rule itself matches FR-RES-03 |
| 2.4 | Readability and tests | The "two callers cannot both win" claim is tested one after the other, not truly in parallel (SP-02 spike covered write contention separately) | **Accepted**: SQLite serialises writes; a real concurrent test is Milestone 11 test-plan work |

## Slice 3: Decide Proposal, auto-path (`src/decide_proposal/service.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 3.1 | Safety | The rule (`confidence < 75` or Severe/Critical) lives in one function, `needs_human`, and is tested at 74/75/90 and Severe/Critical, matching NFR-SEC-02's five cases | No change needed |
| 3.2 | Failure paths | `assign_unit` commits, then the proposal update commits separately. A crash between them leaves a unit `assigned` with a proposal still undecided | **Fixed** (Ben: 'if it's assigned it's approved'): assigning the unit and approving the proposal now happen in one database transaction (auto, human approve and human reject), rolled back together on any error. Tests make the decision save fail on purpose and check the unit is not left assigned. Not done: a database-level trigger enforcing the rule for every writer; that needs a schema change (migration 0002 and a change request), offered to Ben |
| 3.3 | Failure paths | In `POST /reports`, if auto-approve fails with `UNIT_NO_LONGER_AVAILABLE`, the response says `reservation: null` even though the reservation did succeed earlier | **Fixed** (Ben: 'give it a proper error code and find every way it could be lost'): error code `UNIT_LOST_BEFORE_APPROVAL` (reservation still shown in the response), plus one automatic re-reserve and retry (`retried_after_unit_loss`). The ways a unit can vanish between reserving and approving are listed in `decide_auto`'s docstring: the 4-minute clock, a dispatcher rejecting at that moment, a unit taken out of service (future FR-DEGRADE-01 code), or a manual database edit |
| 3.4 | Correctness | A repeated call returns the first decision unchanged (`already_decided`) | No change needed; tested |

## Slice 4: Human decision (`src/decide_proposal/service.py::decide_human`, routes in `src/web_ui/app.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 4.1 | Safety | `POST /proposals/<id>/decision` has no login: anyone who can reach the port can approve a held proposal, and the acting dispatcher is always the seeded `demo-dispatcher` | **Accepted** by Ben as 'a very acceptable gap for a demo as long as it's stated out loud.' The demo script now has the spoken line at the 2:50 beat. Must not ship like this; real login (FR-AUTH-01) is scheduled before Milestone 12 |
| 4.2 | Safety | The caller cannot name the dispatcher (decision comes from the server), so one caller cannot claim to be another | No change needed |
| 4.3 | Correctness | Reject frees only the unit this proposal holds (`release_for_proposal`), tested against another proposal's unit | No change needed |
| 4.4 | Failure paths | Same two-step commit as 3.2 in approve | Covered by the fix for 3.2 (the human approve path is also one transaction) |

## Slice 5: Notify Responder (`src/notify_responder/service.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 5.1 | Correctness | "Notify" is only a database row; no message leaves the machine | **Accepted**: the requirement names no channel (OQ-2); stated in the module, slice log and demo |
| 5.2 | Correctness | FR-ALERT-01 still has "[X] seconds" and TODO acceptance criteria in `docs/requirements.md` | **Defect** in the specification, needs a change request (`docs/change-requests/`), target Milestone 11 |

## Cross-cutting

| # | Pass | Finding | Disposition |
|---|---|---|---|
| X.1 | Readability and tests | Every module takes the database connection as an argument and the model as an argument, so each can be tested with an in-memory/temp database and a fake | No change needed |
| X.2 | Failure paths | During the demo recording, if more than 4 minutes pass between Report B and its approval, the approval fails (see 2.3) | **Accepted**: the script puts the two 40 seconds apart; re-record if it drifts |
| X.3 | Safety | All SQL uses `?` placeholders; the only f-string SQL is a table name in a test helper | No change needed |
| X.4 | Safety | `./script/secrets-check` finds 0 matches; the seed's placeholder password fields say `not-a-real-hash` | No change needed |

## Outside reviewer

Comments and dispositions go in the section below. The reviewer's questions are in `docs/reviews/reviewer-questions.md`.

| Reviewer | Date | Comment | Disposition |
|---|---|---|---|
| (to be filled in) | | | |
