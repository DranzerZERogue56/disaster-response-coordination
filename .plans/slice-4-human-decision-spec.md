# Slice 4 spec: human decision on held proposals (Milestone 10)

Status: decided with Ben, 2026-11-01. Short on purpose.

## Goal
A proposal that slice 3 held (confidence under 75, or Severe/Critical) can be approved or rejected by a dispatcher. Nothing is dispatched without that decision (FR-AGENT-03, NFR-SEC-02).

## Decisions (Ben's answers)
| Question | Answer |
|---|---|
| Dispatcher identity | One seeded fictional `dispatcher_accounts` row (`is_fictional_test_account=1`). Its id goes in `decided_by` (so the audit trail differs from `'auto'`). The route looks it up itself; the caller cannot claim to be someone else. Real login (FR-AUTH-01) replaces only that lookup, later |
| Decisions built | approve and reject. Not modify, not override (FR-RES-02): Milestone 11/12 |
| After reject | `final_status='rejected'`, unit freed immediately, report stays `classified` for a person. No automatic new proposal |
| Interface | JSON only: `GET /proposals/pending`, `POST /proposals/<id>/decision` with `{"decision": "approve"|"reject"}`. No buttons |

## Behaviour
- approve: `assign_unit` (reserved to assigned), then `final_status='approved'`, `decided_by=<dispatcher id>`, `decided_at`. If the reservation was lost: `UNIT_NO_LONGER_AVAILABLE`, nothing decided (HTTP 409).
- reject: free the unit this proposal holds (registry), `final_status='rejected'`, same audit fields.
- Already decided: return the existing decision unchanged (`already_decided`), per the architecture's idempotency rule.
- Errors: `PROPOSAL_NOT_FOUND` (404), `INVALID_DECISION` (400), `STUB_DISPATCHER_MISSING` (500, seed not applied), `UNIT_NO_LONGER_AVAILABLE` (409).
- Observer-role accounts cannot decide (architecture): `NOT_A_DISPATCHER`.

## Out of scope (stated plainly in the demo)
Real login, modify, override with a reason, auto re-proposal after reject, a browser UI, the 45 s dispatcher-response target (NFR-USE-01).

## Acceptance criteria
1. A held proposal shows up in `GET /proposals/pending`; a decided one does not.
2. Approve flips it to `approved`, `decided_by` is the dispatcher id (not `auto`), the unit becomes `assigned`.
3. Reject flips it to `rejected`, the unit is `available` again, the report stays `classified`.
4. A second decision on the same proposal changes nothing.
5. Approving after the reservation expired fails with `UNIT_NO_LONGER_AVAILABLE` and leaves the proposal undecided.
6. An observer account is refused.
