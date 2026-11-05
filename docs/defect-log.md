# Defect Log — Milestone 11

Every defect has all seven fields: (1) ID and title, (2) environment, (3) steps to reproduce, (4) expected versus actual, (5) evidence, (6) severity and priority, assigned separately each with a reason, (7) traceability and status. `tools/verify_regression.py` checks, for every defect marked Fixed, that its named regression test **fails on the commit before the fix and passes now**; the result is in `docs/regression-proof.md`.

**Status of this draft.** The defects, evidence and fixes are real. The severity and priority values are the assistant's proposals for Ben to confirm or change; severity is a fact about the product, priority is Ben's decision about his remaining hours (the template says to write down which hat you wore, so both are stated with a reason).

**Severity:** S1 data loss, security exposure, or the system will not run · S2 a Must requirement is not met and there is no acceptable workaround · S3 a requirement is partly met, or there is a real workaround · S4 cosmetic, wording, or a Could-priority gap.
**Priority:** P1 fix now · P2 fix this iteration · P3 fix if hours remain, otherwise ship as a known defect · P4 will not fix, with the reason.

Environment for all unless stated: Windows 11, Python 3.11.8, SQLite 3.43.1, fake rules model, a fresh seeded database (`seed/iteration-1.sql`), the build at the commit named under "Found at".

## Summary table

| ID | Title | Req | Sev | Pri | Found by | Status | Fix commit | Regression test |
|---|---|---|---|---|---|---|---|---|
| DEF-001 | A report can be classified twice, making a second proposal | FR-AGENT-02 | S3 | P2 | self-review (M10) | Fixed | `c2638bb` | `test_classifying_twice_does_not_make_a_second_proposal` |
| DEF-002 | Expired reservations are only freed when someone next asks, not on a clock | FR-RES-03-AC4 | S2 | P1 | self-review (M10) | Fixed | `068c3ef` | `test_sweeper_frees_an_expired_reservation_with_nobody_asking` |
| DEF-003 | A held proposal whose unit's time ran out stays on the pending list | FR-RES-03-AC4 | S3 | P2 | self-review (M10) | Fixed | `b8c124e` | `test_a_held_proposal_whose_clock_runs_out_times_out_and_leaves_the_pending_list` |
| DEF-004 | Approving saves the unit and the decision separately; a stop between leaves them disagreeing | FR-AGENT-03 | S2 | P1 | self-review (M10) | Fixed | `068c3ef` | `test_auto_approve_failing_midway_does_not_leave_an_assigned_unit` |
| DEF-005 | When auto-approval loses the unit, the response says no reservation was made | FR-RES-01-AC2 | S4 | P3 | self-review (M10) | Fixed | `068c3ef` | `test_unit_lost_twice_gets_its_own_error_code_and_dispatches_nothing` |
| DEF-006 | Offline queue orders reports by time written as text, wrong across time zones | FR-INTAKE-01-AC2 | S2 | P1 | self-review (M10) | Fixed | `b8c124e` | `test_offline_queue_orders_by_real_time_across_time_zones` |
| DEF-007 | The override log (and its follow-up) can be edited after the fact | FR-AUDIT-02 | S2 | P2 | self-review (M10) | Fixed | `4eaa83e` | `test_the_override_log_and_its_follow_ups_cannot_be_edited` |
| DEF-008 | Two Must requirements contain a literal "[X] seconds", so cannot be tested | FR-ALERT-01, FR-INFER-02 | S3 | P2 | test planning (M11) | Fixed | `d51b9e0` | `test_no_must_requirement_sentence_contains_a_placeholder` |
| DEF-009 | A JSON list or string body crashes the intake route with HTTP 500 | FR-INTAKE-02 | S2 | P1 | hostile test data (M11) | Fixed | `4f4a5cc` | `test_a_body_that_is_not_a_json_object_is_refused_not_crashed` |
| DEF-010 | A list or object where text belongs crashes the intake route with HTTP 500 | FR-INTAKE-02 | S2 | P1 | hostile test data (M11) | Fixed | `4f4a5cc` | `test_a_list_or_object_where_text_belongs_is_invalid_not_a_crash` |
| DEF-011 | Whitespace-only text is accepted as a valid location or description | FR-INTAKE-02 | S3 | P2 | hostile test data (M11) | Fixed | `4f4a5cc` | `test_whitespace_only_text_is_invalid` |
| DEF-012 | A number or boolean is accepted as text | FR-INTAKE-02 | S3 | P2 | hostile test data (M11) | Fixed | `4f4a5cc` | `test_a_number_or_boolean_is_not_accepted_as_text` |
| DEF-013 | A dispatcher's approval gives no second path when the held unit was lost | FR-RES-01-AC2 | S2 | P2 | acceptance test (M11) | Fixed | `9607340` | `test_a_lost_unit_is_replaced_by_an_alternative_when_the_dispatcher_approves` |
| DEF-014 | The proposal log does not record the input data the agent used | FR-AUDIT-01-AC1 | S3 | P2 | acceptance test (M11) | Fixed | `9607340` | `test_the_proposal_records_the_input_data_and_the_confidence_when_it_is_generated` |
| DEF-015 | The model-answer validator accepts non-text reasoning and boolean confidence | FR-AGENT-01-AC2 | S3 | P2 | property test (M11) | Fixed | `4a0afc2` | `test_reasoning_must_be_non_empty_text` |
| DEF-016 | Unit status changes and reservations are not sent to "every agent" (no agents exist) | FR-RES-03-AC1..AC3 | S3 | P3 | traceability gap (M11) | Open | none | none (not built) |
| DEF-017 | "Notify" only records a row; there is no way to notify a responder from the software | FR-ALERT-01 | S3 | P3 | peer reviewer (M10, Q10) | Open | none | none (needs a channel decision) |
| DEF-018 | Anyone who can reach the server can approve or override; there is no login | FR-AUTH-01-AC2 | S2 | P2 | acceptance test (M11) | Open | none | `test_FR_AUTH_01_AC2_an_unauthenticated_caller_cannot_approve` (expected to fail) |
| DEF-019 | No length limit: a 100,000-character location is accepted and stored | FR-INTAKE-02 | S4 | P4 | hostile test data (M11) | Will not fix | none | `test_hostile_text_that_is_accepted_is_stored_exactly_as_sent[100k-character-location]` (passes: stored safely) |
| DEF-020 | A report timestamped in the year 2099 is accepted | FR-INTAKE-02 | S4 | P3 | hostile test data (M11) | Open | none | `test_hostile_text_that_is_accepted_is_stored_exactly_as_sent[far-future-time]` (passes: stored safely) |

---

## Defect reports

### DEF-001 — A report can be classified twice, making a second proposal
- **Environment:** commit `bd53194`; seeded database.
- **Steps:** 1. Submit a report (it is classified). 2. Call Classify & Propose again with the same report id.
- **Expected vs actual:** Expected: refused, one proposal per report. Actual: a second `agent_proposals` row, a second recommendation.
- **Evidence:** found by reading the code in the Milestone 10 self-review (finding 1.1); `tests/unit/test_classify_propose.py::test_classifying_twice_does_not_make_a_second_proposal`.
- **Severity S3:** FR-AGENT-02 is partly met and no dispatch happens twice; **Priority P2:** cheap to fix and on the demo path.
- **Traceability and status:** FR-AGENT-02-AC1; Fixed in `c2638bb` (`ALREADY_CLASSIFIED`). Owner: Ben.

### DEF-002 — Expired reservations are only freed when someone next asks
- **Environment:** commit `fdee37b`.
- **Steps:** 1. Submit a vague report (confidence 40): its unit is reserved and the proposal is held. 2. Wait more than 4 minutes and send no other request.
- **Expected vs actual:** Expected: the unit returns to available within 4 minutes (FR-RES-03-AC4, NFR-REL-02). Actual: it stays reserved until the next reservation request.
- **Evidence:** self-review finding 2.2; `tests/integration/test_clock_and_atomicity_http.py::test_sweeper_frees_an_expired_reservation_with_nobody_asking`.
- **Severity S2:** a Must requirement's timing is not met with no workaround short of sending a request; **Priority P1:** Ben asked for a visible, running clock.
- **Traceability and status:** FR-RES-03-AC4, NFR-REL-02-AC1; Fixed in `068c3ef` (5-second sweeper, `/units` clock). Owner: Ben.

### DEF-003 — A held proposal whose unit's time ran out stays on the pending list
- **Environment:** commit `a98ea9a`.
- **Steps:** 1. Hold a proposal (confidence 40). 2. Let its 4 minutes pass. 3. List pending proposals, then approve.
- **Expected vs actual:** Expected: the proposal times out and leaves the list. Actual: it stayed listed with no unit; approving failed with `UNIT_NO_LONGER_AVAILABLE`.
- **Evidence:** self-review finding 2.3; `tests/unit/test_human_decision.py::test_a_held_proposal_whose_clock_runs_out_times_out_and_leaves_the_pending_list`.
- **Severity S3:** a dispatcher could be asked to approve something already dead; no wrong dispatch occurs; **Priority P2.**
- **Traceability and status:** FR-RES-03-AC4; Fixed in `b8c124e` (`rejected` / `timeout`). Owner: Ben.

### DEF-004 — Approving saves the unit and the decision separately
- **Environment:** commit `353b437`.
- **Steps:** 1. Auto-approve a proposal. 2. Make the second save (the proposal update) fail.
- **Expected vs actual:** Expected: both saved or neither. Actual: the unit stayed `assigned` while the proposal stayed undecided.
- **Evidence:** self-review finding 3.2; `tests/unit/test_clock_and_atomicity.py::test_auto_approve_failing_midway_does_not_leave_an_assigned_unit`.
- **Severity S2:** a dispatch without an approved proposal violates NFR-SEC-02; **Priority P1.**
- **Traceability and status:** FR-AGENT-03, NFR-SEC-02; Fixed in `068c3ef` (one transaction), then enforced by the database in `fb08be3` (CR-001). Owner: Ben.

### DEF-005 — When auto-approval loses the unit, the response says no reservation was made
- **Environment:** commit `a98ea9a`.
- **Steps:** 1. Reserve succeeds. 2. The unit is lost before the automatic approval finishes.
- **Expected vs actual:** Expected: an error that says the unit was lost, with the reservation shown. Actual: `reservation: null` and a generic error.
- **Evidence:** self-review finding 3.3; `tests/integration/test_clock_and_atomicity_http.py::test_unit_lost_twice_gets_its_own_error_code_and_dispatches_nothing`.
- **Severity S4:** a misleading message only; nothing wrongly dispatched; **Priority P3.**
- **Traceability and status:** FR-RES-01-AC2; Fixed in `068c3ef` (`UNIT_LOST_BEFORE_APPROVAL`, one automatic retry). Owner: Ben.

### DEF-006 — Offline queue orders reports by time written as text
- **Environment:** commit `65d343b`.
- **Steps:** 1. Go offline. 2. Submit a report stamped `2026-11-01T07:30:00-05:00` (12:30 UTC) and one stamped `2026-11-01T12:10:00Z`. 3. Reconnect.
- **Expected vs actual:** Expected: the 12:10 report first (oldest). Actual: the text sorts `07:30...` first, so the later report was processed first.
- **Evidence:** self-review finding 6.4; `tests/integration/test_timestamps_and_concurrency_http.py::test_offline_queue_orders_by_real_time_across_time_zones`, and property test P2.
- **Severity S2:** FR-INTAKE-01-AC2 requires timestamp order; **Priority P1.**
- **Traceability and status:** FR-INTAKE-01-AC2; Fixed in `b8c124e` (times stored as UTC). Owner: Ben.

### DEF-007 — The override log can be edited after the fact
- **Environment:** commit `a16e311`.
- **Steps:** 1. Record an override with a follow-up. 2. Edit the follow-up or the override reason directly.
- **Expected vs actual:** Expected: data can only be added, never changed or removed (Ben's FR-AUDIT-02 criterion). Actual: the follow-up rewrote the same row, so the log was rewritable.
- **Evidence:** self-review finding 7.2; `tests/unit/test_override_assignment.py::test_the_override_log_and_its_follow_ups_cannot_be_edited`.
- **Severity S2:** an editable audit trail defeats FR-AUDIT-02; **Priority P2.**
- **Traceability and status:** FR-AUDIT-02-AC2; Fixed in `4eaa83e` (append-only table, CR-002). Owner: Ben.

### DEF-008 — Two Must requirements contain a literal "[X] seconds"
- **Environment:** `docs/requirements.md` v1.3 at `bbcae34`.
- **Steps:** 1. Read FR-ALERT-01 and FR-INFER-02.
- **Expected vs actual:** Expected: a number that a test can check. Actual: "within [X] seconds", so neither requirement could be tested.
- **Evidence:** found while writing the test plan; `tests/unit/test_spec_checks.py::test_no_must_requirement_sentence_contains_a_placeholder`.
- **Severity S3:** two Must requirements untestable (a specification defect, not a code defect); **Priority P2.**
- **Traceability and status:** FR-ALERT-01, FR-INFER-02; Fixed in `d51b9e0` (CR-003: 10 seconds and 5 seconds, Ben's numbers). Owner: Ben.

### DEF-009 — A JSON list or string body crashes the intake route with HTTP 500
- **Environment:** commit `0e9cfdf`; hostile data family.
- **Steps:** 1. `POST /reports` with a body of `[1, 2, 3]` or `"just a string"`.
- **Expected vs actual:** Expected: HTTP 400 rejecting the report. Actual: HTTP 500 (`AttributeError: 'list' object has no attribute 'get'`).
- **Evidence:** `tests/integration/test_data_families_http.py` entries `json-list-instead-of-object`, `json-string-instead-of-object` (strict xfail at `d51b9e0`).
- **Severity S2:** FR-INTAKE-02 says bad input is rejected, and a crash is not a rejection; the sender gets no usable answer; **Priority P1:** it is the front door.
- **Traceability and status:** FR-INTAKE-02-AC1; Fixed in `4f4a5cc` (`INVALID_BODY`, HTTP 400). Owner: Ben.

### DEF-010 — A list or object where text belongs crashes the intake route
- **Environment:** commit `0e9cfdf`; hostile data family.
- **Steps:** 1. `POST /reports` with `severity_raw` as a list, `location` as an object, or deeply nested lists.
- **Expected vs actual:** Expected: HTTP 400 naming the field. Actual: HTTP 500 (`sqlite3.ProgrammingError: Error binding parameter`).
- **Evidence:** entries `list-as-severity`, `object-as-location`, `deeply-nested-values`.
- **Severity S2:** same reasoning as DEF-009; **Priority P1.**
- **Traceability and status:** FR-INTAKE-02-AC1; Fixed in `4f4a5cc` (`FIELD_INVALID`). Owner: Ben.

### DEF-011 — Whitespace-only text is accepted
- **Environment:** commit `0e9cfdf`; hostile data family.
- **Steps:** 1. `POST /reports` with `location` of three spaces, or `severity_raw` of a tab and a newline.
- **Expected vs actual:** Expected: rejected as improperly filled. Actual: HTTP 201, a report with an empty-looking location.
- **Evidence:** entries `whitespace-only-location`, `whitespace-only-severity`.
- **Severity S3:** the requirement is partly met (a truly empty field is rejected) and a dispatcher can phone for the location; **Priority P2.**
- **Traceability and status:** FR-INTAKE-02-AC1; Fixed in `4f4a5cc`. Owner: Ben.

### DEF-012 — A number or boolean is accepted as text
- **Environment:** commit `0e9cfdf`; hostile data family.
- **Steps:** 1. `POST /reports` with `location: 123` or `reporting_unit: true`.
- **Expected vs actual:** Expected: rejected. Actual: HTTP 201, the value stored as if it were text.
- **Evidence:** entries `number-as-location`, `boolean-as-reporting-unit`.
- **Severity S3:** wrong data stored, nothing dispatched on it directly; **Priority P2.**
- **Traceability and status:** FR-INTAKE-02-AC1; Fixed in `4f4a5cc`. Owner: Ben.

### DEF-013 — A dispatcher's approval gives no second path when the held unit was lost
- **Environment:** commit `0e9cfdf`; acceptance test.
- **Steps:** 1. Submit a vague report (held, unit reserved). 2. The unit becomes unavailable. 3. The dispatcher approves.
- **Expected vs actual:** Expected (FR-RES-01-AC2): a second path to a responder instead of leaving the incident without one. Actual: HTTP 409; nothing assigned; the incident has no responder.
- **Evidence:** `tests/acceptance/test_acceptance_criteria.py::test_FR_RES_01_AC2_...` (strict xfail at `0e9cfdf`).
- **Severity S2:** a Must criterion not met on the human path, with no workaround except a second manual approval; **Priority P2.**
- **Traceability and status:** FR-RES-01-AC2; Fixed in `9607340` (the alternatives are tried, then approved). Owner: Ben.

### DEF-014 — The proposal log does not record the input data the agent used
- **Environment:** commit `0e9cfdf`; acceptance test.
- **Steps:** 1. Submit a report. 2. Read the proposal's log entry.
- **Expected vs actual:** Expected (Ben's FR-AUDIT-01 criterion): the entry includes the input data and the confidence. Actual: confidence and reasoning, but only a pointer (`report_id`) to the input, a row that can change or be purged after 24 hours.
- **Evidence:** `tests/acceptance/test_acceptance_criteria.py::test_FR_AUDIT_01_AC1_...` (strict xfail at `0e9cfdf`).
- **Severity S3:** the audit is partly met; **Priority P2.**
- **Traceability and status:** FR-AUDIT-01-AC1; Fixed in `9607340` (migration 0004, CR-004: a snapshot that cannot be changed). Owner: Ben.

### DEF-015 — The model-answer validator accepts non-text reasoning and boolean confidence
- **Environment:** commit `b20aa94`; property test P4.
- **Steps:** 1. Give the validator an answer with `reasoning: None` (or a number or list), or `confidence: true`.
- **Expected vs actual:** Expected: refused (`MODEL_OUTPUT_INVALID`). Actual: accepted; `None` became the text "None".
- **Evidence:** Hypothesis's failing example `{'severity': 'Minor', 'unit_type': 'Medical', 'confidence': 0, 'reasoning': None}`; `tests/unit/test_properties.py::test_P4_...` (strict xfail at `b20aa94`).
- **Severity S3:** a malformed model answer could be stored as a proposal; the real model is not wired in yet; **Priority P2.**
- **Traceability and status:** FR-AGENT-01-AC2; Fixed in `4a0afc2`. Owner: Ben.

### DEF-016 — Status changes and reservations are not sent to "every agent"
- **Environment:** commit `4a0afc2`.
- **Steps:** 1. Read FR-RES-03-AC1 to AC3 ("every agent sees the updated status", "sent to the other agents"). 2. Look for agents.
- **Expected vs actual:** Expected: other agents receive status and reservation updates. Actual: there are no separate agents; one process and one database are the single source of truth.
- **Evidence:** the three criteria show as gaps in `docs/traceability.csv`; no test is possible without agents.
- **Severity S3:** the safety effect (no double-booking) is met by the database and the property test P3; the broadcast is not; **Priority P3:** scheduled with the negotiation work (Milestone 12).
- **Traceability and status:** FR-RES-03-AC1, AC2, AC3; Open; workaround: the registry is the only writer. Owner: Ben.

### DEF-017 — "Notify" only records a row; the software cannot notify a responder
- **Environment:** commit `4a0afc2`.
- **Steps:** 1. Auto-approve a proposal. 2. Look for a message sent to the unit.
- **Expected vs actual:** Expected (FR-ALERT-01): the responder is notified. Actual: a `notifications` row is written; nothing leaves the machine.
- **Evidence:** self-review finding 5.1; the peer reviewer's answer to Q10: "there should be a way to do it in the software".
- **Severity S3:** a real workaround (the dispatcher notifies outside the software); **Priority P3:** the delivery channel is an open design question (OQ-2).
- **Traceability and status:** FR-ALERT-01-AC1 is met only as "recorded within 10 seconds"; Open. Owner: Ben.

### DEF-018 — There is no login: anyone who reaches the server can approve or override
- **Environment:** commit `4a0afc2`; acceptance test.
- **Steps:** 1. Start the app. 2. Send `POST /proposals/1/decision` with no credentials.
- **Expected vs actual:** Expected (FR-AUTH-01-AC2): an action outside the caller's role is refused. Actual: it is accepted, always as the stand-in dispatcher.
- **Evidence:** `tests/acceptance/test_acceptance_criteria.py::test_FR_AUTH_01_AC2_an_unauthenticated_caller_cannot_approve` (strict xfail).
- **Severity S2:** a decision that dispatches a unit with no authentication; **Priority P2:** FR-AUTH-01 is Should this release, the app listens only on 127.0.0.1, and the demo says so aloud; real login is planned before Milestone 12.
- **Traceability and status:** FR-AUTH-01-AC2; Open; workaround: bind to localhost only. Must not ship v1.0 like this. Owner: Ben.

### DEF-019 — No length limit on text fields
- **Environment:** commit `4a0afc2`; hostile data family.
- **Steps:** 1. `POST /reports` with a 100,000-character `location`.
- **Expected vs actual:** Expected: no requirement says. Actual: accepted and stored exactly as sent, with no crash.
- **Evidence:** hostile entries `10k-character-severity`, `100k-character-location` pass.
- **Severity S4:** nothing is lost or exposed; the database copes; **Priority P4:** will not fix this release, because no requirement sets a limit and adding one would be an invented requirement; revisit if a real feed shows long text.
- **Traceability and status:** FR-INTAKE-02 (silent on length); Will not fix. Owner: Ben.

### DEF-020 — A report timestamped in the year 2099 is accepted
- **Environment:** commit `4a0afc2`; hostile data family.
- **Steps:** 1. `POST /reports` with `timestamp_reported` of `2099-01-01T00:00:00+00:00`.
- **Expected vs actual:** Expected: the specification does not say whether the future is a "bad value". Actual: accepted and stored as UTC.
- **Evidence:** hostile entry `far-future-time` passes (marked "safe", not "reject", on purpose).
- **Severity S4:** a far-future time sorts last in the queue and misleads nobody into a wrong dispatch (workaround: the dispatcher reads the report time on the page and the queue is oldest-first); **Priority P3:** needs Ben's decision on whether FR-INTAKE-02 should reject times more than some margin ahead.
- **Traceability and status:** FR-INTAKE-02; Open. Owner: Ben.
