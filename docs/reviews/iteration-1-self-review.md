# Iteration 1 self-review (Milestone 10)

**Status: DRAFT written by the AI assistant, 2026-11-01. Ben has not yet corrected it.** Every finding below must be checked by Ben against the code before this file counts as his review. Where he disagrees, he changes the disposition and says why.

**About the four passes:** the assignment asks for "the four passes" but does not define them in the text or in the course's `10-iteration-one-building-the-core/code` folder that I could reach. Ben's decision (2026-11-01): keep these four, reworded in plain language. If the textbook names different ones, rename the headings.

1. **Does what was asked:** does the code do what the acceptance criteria say?
2. **When things go wrong:** what happens when inputs, timing or neighbouring parts fail?
3. **Misuse and bypass:** can the safety rule or a boundary be got around?
4. **Readable and trustworthy:** could a stranger follow it, and do the tests actually prove it?

Dispositions: **Fixed** (with commit), **Defect** (logged in `docs/review/review-defect-log.csv` style, with a target), **Accepted** (with a written reason).

## Slice 1: Classify & Propose (`src/classify_propose/`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 1.1 | Does what was asked | Classifying the same report twice would insert a second proposal for it (no check on report status) | **Fixed** this session: `ALREADY_CLASSIFIED` error plus `test_classifying_twice_does_not_make_a_second_proposal` |
| 1.2 | When things go wrong | A model answer with a bad severity, unit type, confidence or empty reasoning is rejected and the report is left for a human | No change needed; covered by `test_invalid_model_output_leaves_report_for_a_human` |
| 1.3 | Does what was asked | The 5-second limit (FR-AGENT-01) is not measured; the fake model answers instantly | **Accepted**, and the method is now built: `python -m src.classify_propose.measure` runs NFR-PERF-01's own method (20 seeded reports, p95). On the fake model p95 is about 5 ms (`docs/measurements.md`), which proves the path and the method, not a real model's speed. Still unmet until it is run with Ollama on the target machine |
| 1.4 | Readable and trustworthy | `FakeModel` matches word fragments (for example "gun" would match "begun", "conscious" matches "unconscious"), so it can mislabel unusual wording | **Accepted**: it is a stand-in whose only job is to be predictable for tests and the demo; it will be replaced |
| 1.5 | Misuse and bypass | The confidence number comes from the model itself, and a small model's self-reported confidence can be unreliable | **Accepted** (Ben: tune Report B when the real model arrives) **and measured** (Ben: also add a calibration measurement): `docs/measurements.md` records the confidence spread (40 / 77.0 / 95) and the share routed to a person (40%, against ADR 0001's 40% revisit line) on the fake model |

## Slice 2: Unit Registry (`src/unit_registry/service.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 2.1 | Does what was asked | Reserving is one conditional UPDATE that only matches an available unit, so two requests cannot both win | No change needed; covered by `test_reserving_a_reserved_unit_raises_unit_already_reserved` (sequential only, see 2.4) |
| 2.2 | When things go wrong | Expired reservations are freed only when someone next asks to reserve; there is no timer, so NFR-REL-02's "within 4 minutes" holds only while traffic arrives | **Fixed** (Ben: 'there should be a set clock anyone using the software can see'): a background sweeper frees expired reservations every 5 s (`SWEEP_SECONDS`, started by `script/start`), `unit_clock()` and `GET /units` show each unit's `frees_at` and `seconds_left`, and the `/reports` page shows the same table, refreshing every 5 s. Tests in `tests/test_clock_and_atomicity.py` |
| 2.3 | When things go wrong | A proposal held for a human loses its unit after 4 minutes and still shows in `/proposals/pending`; approving it then fails with `UNIT_NO_LONGER_AVAILABLE` | **Fixed** (Ben: fix now): a held proposal whose unit's 4-minute clock runs out is timed out (`final_status` `rejected`, `decided_by` `timeout`) and leaves the pending list; approving it afterwards changes nothing. Tests in `tests/test_human_decision.py` |
| 2.4 | Readable and trustworthy | The "two callers cannot both win" claim is tested one after the other, not truly in parallel (SP-02 spike covered write contention separately) | **Fixed** (Ben: add a threaded test now): `tests/test_timestamps_and_concurrency.py` has eight threads, each on its own database connection, reserving the same unit at once. Exactly one wins and seven get `UNIT_ALREADY_RESERVED` |

## Slice 3: Decide Proposal, auto-path (`src/decide_proposal/service.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 3.1 | Misuse and bypass | The rule (`confidence < 75` or Severe/Critical) lives in one function, `needs_human`, and is tested at 74/75/90 and Severe/Critical, matching NFR-SEC-02's five cases | No change needed |
| 3.2 | When things go wrong | `assign_unit` commits, then the proposal update commits separately. A crash between them leaves a unit `assigned` with a proposal still undecided | **Fixed** twice. (1) Ben: "if it's assigned it's approved": assigning the unit and approving the proposal are one transaction (auto, human approve, human reject), tested by making the decision save fail on purpose. (2) Ben then asked for database-level enforcement: migration `0002` adds triggers so the database refuses an assigned unit whose proposal is not approved, for every writer (CR-001), tested with direct SQL |
| 3.3 | When things go wrong | In `POST /reports`, if auto-approve fails with `UNIT_NO_LONGER_AVAILABLE`, the response says `reservation: null` even though the reservation did succeed earlier | **Fixed** (Ben: 'give it a proper error code and find every way it could be lost'): error code `UNIT_LOST_BEFORE_APPROVAL` (reservation still shown in the response), plus one automatic re-reserve and retry (`retried_after_unit_loss`). The ways a unit can vanish between reserving and approving are listed in `decide_auto`'s docstring: the 4-minute clock, a dispatcher rejecting at that moment, a unit taken out of service (future FR-DEGRADE-01 code), or a manual database edit |
| 3.4 | Does what was asked | A repeated call returns the first decision unchanged (`already_decided`) | No change needed; tested |

## Slice 4: Human decision (`src/decide_proposal/service.py::decide_human`, routes in `src/web_ui/app.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 4.1 | Misuse and bypass | `POST /proposals/<id>/decision` has no login: anyone who can reach the port can approve a held proposal, and the acting dispatcher is always the seeded `demo-dispatcher` | **Accepted** by Ben as 'a very acceptable gap for a demo as long as it's stated out loud.' The demo script now has the spoken line at the 2:50 beat. Must not ship like this; real login (FR-AUTH-01) is scheduled before Milestone 12 |
| 4.2 | Misuse and bypass | The caller cannot name the dispatcher (decision comes from the server), so one caller cannot claim to be another | No change needed |
| 4.3 | Does what was asked | Reject frees only the unit this proposal holds (`release_for_proposal`), tested against another proposal's unit | No change needed |
| 4.4 | When things go wrong | Same two-step commit as 3.2 in approve | Covered by the fix for 3.2 (the human approve path is also one transaction) |

## Slice 5: Notify Responder (`src/notify_responder/service.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 5.1 | Does what was asked | "Notify" is only a database row; no message leaves the machine | **Accepted**: the requirement names no channel (OQ-2); stated in the module, slice log and demo |
| 5.2 | Does what was asked | FR-ALERT-01 still has "[X] seconds" and TODO acceptance criteria in `docs/requirements.md` | **Defect** in the specification, needs a change request (`docs/change-requests/`), target Milestone 11 |

## Slice 6: Offline queue (`src/intake_gateway/queue.py`, `/connectivity` in `src/web_ui/app.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 6.1 | When things go wrong | The connectivity switch is a variable in the running process: it resets to "connected" on restart and would not be shared by several server processes | **Accepted** (Ben): one dev server process; the queue itself is in the database and survives a restart. Revisit at Milestone 14 (deployment) |
| 6.2 | When things go wrong | Draining happens inside the one request that reconnects, so a very long queue makes that request slow | **Accepted**: 10 reports (NFR-REL-03) is instant; a background drain is a Milestone 12 option if NFR-REL-04's 100 reports needs it |
| 6.3 | Does what was asked | No maximum queue size | **Accepted**: the spec leaves it open (OQ-1); stated in the module |
| 6.4 | Does what was asked | Reports are ordered by `timestamp_reported` as text. Mixed time zones (a `-05:00` stamp next to a `Z` stamp) or different formats could sort wrongly | **Fixed** (Ben: fix now): `timestamp_reported` is normalised to UTC at intake (no offset is taken as UTC; a non-ISO time is refused with `INVALID_TIMESTAMP`), so the queue drains in real time order across time zones. Tests include a `-05:00` report that sorts after a `Z` report it would have beaten as text |
| 6.5 | Does what was asked | A queued report that finds no free unit is not lost: it stays `created` and the reconnection response names the error | No change needed; tested (4 reports, 2 units) |

## Slice 7: Override Assignment (`src/override_assignment/service.py`)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| 7.1 | When things go wrong | The override, the unit swap and the log row happen in one transaction; a taken unit leaves the original assignment and the log untouched | No change needed; tested |
| 7.2 | Does what was asked | The follow-up edits the same log row as FR-RES-02 asks, so the override log is not append-only (T-6.1 asks for that for proposals) | **Fixed** (Ben: separate follow-ups table, CR-002): each follow-up is a row in `override_follow_ups` (migration 0003), and triggers refuse any edit of that table or of `dispatcher_overrides`. The old column is left in place, unused. Deleting stays possible for the 24-hour purge job |
| 7.3 | Misuse and bypass | An observer's blocked attempt is refused but not logged (needs real login, FR-AUTH-01) | **Defect**, same target as 4.1 |
| 7.4 | Does what was asked | A dispatcher can override to a unit of a different type (for example Fire for a Medical incident) with no warning | **Accepted** (Ben): FR-RES-02 says "any assignment, at any time"; the reason is the control |
| 7.5 | Readable and trustworthy | `modified` now means two things: a dispatcher changed the unit at approval, or after the fact | **Accepted**: both mean "a person chose a different unit"; recorded in CR-001 |

## Database rule (CR-001)

| # | Pass | Finding | Disposition |
|---|---|---|---|
| D.1 | Does what was asked | The first version of the trigger did not fire when the proposal was undecided, because comparing NULL to a list is neither true nor false | **Fixed** in the same session (`COALESCE`), found by `tests/test_database_rule.py` before the commit |

## Cross-cutting

| # | Pass | Finding | Disposition |
|---|---|---|---|
| X.1 | Readable and trustworthy | Every module takes the database connection as an argument and the model as an argument, so each can be tested with an in-memory/temp database and a fake | No change needed |
| X.2 | When things go wrong | During the demo recording, if more than 4 minutes pass between Report B and its approval, the approval fails (see 2.3) | **Accepted**: the script puts the two 40 seconds apart; re-record if it drifts |
| X.3 | Misuse and bypass | All SQL uses `?` placeholders; the only f-string SQL is a table name in a test helper | No change needed |
| X.4 | Misuse and bypass | `./script/secrets-check` finds 0 matches; the seed's placeholder password fields say `not-a-real-hash` | No change needed |

## Ben's decisions in the self-review question round (2026-11-01)

| # | Finding | Ben's decision |
|---|---|---|
| B1 | The four passes | Keep the assistant's four, reworded in plainer language |
| B2 | 2.3 held proposal expiring | Fix now (done) |
| B3 | 6.4 timestamp order | Fix now: normalise to UTC (done) |
| B4 | 7.2 follow-up log | Fix now with a separate table (done, CR-002) |
| B5 | 7.4 override to a different unit type | Accept |
| B6 | 6.1 connectivity switch in memory | Accept for the dev server |
| B7 | 2.4 concurrency claim | Add a threaded test now (done) |
| B8 | 1.5 model-reported confidence | Accept, and add a measurement (done: `docs/measurements.md`) |
| B9 | Every item marked "No change needed" | Agreed |
| B10 | Reviewer in the table | Anonymous: "peer reviewer" |

## Outside reviewer

Comments and dispositions go in the section below. The reviewer's questions are in `docs/reviews/reviewer-questions.md`.

| Reviewer | Date | Comment | Disposition |
|---|---|---|---|
| Peer reviewer (name withheld) | 2026-11-01 | Q1: the validator only checks shape; any data could technically pass, so answers that pass are more likely right, and prompt engineering can raise accuracy further | **Accepted**: that is how it is meant to work. Noted for the Ollama work (schema validator plus one retry, GitHub issue #5) |
| Peer reviewer | 2026-11-01 | Q2: "propose the best remaining unit" is correct; it must offer at least an option | No change needed: matches FR-AGENT-02 criterion 2 |
| Peer reviewer | 2026-11-01 | Q3: swapping the model is clear | No change needed |
| Peer reviewer | 2026-11-01 | Q4: two requests cannot both hold a unit | No change needed; also covered by the eight-thread test |
| Peer reviewer | 2026-11-01 | Q6: nothing else reads the old recommended unit and gets confused | No change needed |
| Peer reviewer | 2026-11-01 | Q7: nothing is dispatched without a person | No change needed; backed by the safety-rule table and the database rule (CR-001) |
| Peer reviewer | 2026-11-01 | Q10: the dispatcher can always notify a unit outside the software, but there should be a way to do it inside the software | **Accepted, deferred**: a real delivery channel is the open question OQ-2 (finding 5.1); the demo and docs say "notify" is a database row only. Needs a change request to finish FR-ALERT-01 |
| Peer reviewer | 2026-11-01 | Q11: calling notify a record only is honest enough | No change needed |
| Peer reviewer | 2026-11-01 | Q12: no obvious bug that a test would not catch | No change needed (the reviewer did not name a test; the self-review's own gaps stand) |
| Peer reviewer | 2026-11-01 | Q13: no commit message fails to explain why | No change needed |
| Peer reviewer | 2026-11-01 | Q14: reports entered with a different time zone could be ordered wrongly | **Fixed** before this answer was recorded (finding 6.4): times are stored in UTC and a mixed-time-zone queue test passes |
| Peer reviewer | 2026-11-01 | Q15: a half-done override cannot be left behind | No change needed; the override is one transaction (finding 7.1) |
| Peer reviewer | 2026-11-01 | Q16: the database rules cannot block anything legitimate | No change needed |
| Peer reviewer | 2026-11-01 | Q5, Q8: already fixed by Ben. Q9: no answer | Recorded as given; the matching of these three is uncertain (see the note in `reviewer-questions.md`) |
