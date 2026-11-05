# CR-003 — Acceptance criteria written for six Must requirements; two "[X] seconds" placeholders filled

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, `docs/requirements.md` v1.3 to v1.4 |
| Trigger | Milestone 11 test planning. Six Must requirements still had only `TODO` placeholders where their acceptance criteria belong, and two of them (FR-ALERT-01, FR-INFER-02) had a literal "[X] seconds" in the requirement sentence itself, so neither could be tested as written |

## What changes
In `docs/requirements.md`:

| Requirement | Before | After |
|---|---|---|
| FR-ALERT-01 | "within [X] seconds"; criteria `TODO` | "within 10 seconds" (Ben: "X's 10 seconds"); one criterion written; failure-case criterion still `TODO` |
| FR-INFER-02 | "within [X] seconds"; criteria `TODO` | "within 5 seconds" (Ben: "Do 5 seconds"); one criterion written; failure-case criterion still `TODO` |
| FR-AUDIT-01 | criteria `TODO` | one criterion written; failure case `TODO` |
| FR-AUDIT-02 | criteria `TODO` | two criteria written |
| FR-SIM-01 | criteria `TODO` | one criterion written; pace criterion `TODO` |
| FR-INFER-01 | criteria `TODO` | one criterion written; second criterion `TODO` |

Ben's answers, as given in chat on 2026-11-05 (the criteria are a restatement of these in Given/when/then form; the numbers and ideas are his):
- FR-ALERT-01: "X's 10 seconds."
- FR-AUDIT-02: "it can be edited afterwards only to add more data not take away."
- FR-AUDIT-01: "It should include input data."
- FR-SIM-01: "If you give it the same scenario 3 times without it being trained, it should always be able to have the same confidence score or a very similar one at the least."
- FR-INFER-01: "if I trust them with the .env file, if I don't, they should be able to find our console logs and see API calls." (taken to mean: the logs show no external API calls)
- FR-INFER-02: "Do 5 seconds."

Five other non-Must requirements still have placeholders (FR-INFER-03, FR-INFER-04, FR-ALERT-02, FR-MAP-01, FR-MAP-02). They are not changed here; they appear in the traceability matrix as visible gaps.

## Why
A Must requirement with no acceptance criterion cannot be verified, and a requirement with "[X]" in it cannot be tested at all. Milestone 11 asks for every Must to be traced to a test; this makes six of them traceable, and shows the remaining gaps instead of hiding them.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-ALERT-01, FR-AUDIT-01, FR-AUDIT-02, FR-SIM-01, FR-INFER-01, FR-INFER-02 |
| Specification sections affected | `docs/requirements.md` section 5 (version 1.4) |
| Hours: added / removed | +0.5 / -0 |
| Schedule effect | none |
| Risk effect | exposes work not yet built: three of the six (FR-SIM-01, FR-INFER-01, FR-INFER-02 on a real model) cannot pass yet and will show as gaps or failures |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-05 |
| Rationale | Needed to make the Must set testable. The values come from Ben. The wording into Given/when/then was done by the assistant from his statements and is for Ben to confirm; this milestone's AI policy lets an assistant propose test material, but the requirements policy (Milestone 3) says a requirement sentence must be the author's, so the note under each criterion says where the wording came from |

## Applied

- [x] Specification updated and committed
- [x] Traceability matrix: rebuilt as `docs/traceability.csv` (criterion level) in Milestone 11
- [x] Plan and hours re-baselined: not needed (+0.5 h, under the 4 h threshold)
- [x] Row added to `CHANGELOG.md`
- [x] New baseline tag: not created. Ben to decide whether filling in criteria counts as a Must change (spec-baseline-v1.1)

## Second round (2026-11-05, later the same day)

Ben asked what the failure-case criteria should be. The assistant proposed three, Ben said "I like the 3 proposed ideas" and asked for the FR-ALERT-01 one to be more explicit. He also asked for a rough hypothesis of what the FR-SIM-01 pace criterion will look like, and for the FR-INFER-02 second criterion to be left open with a note saying why. All five are now in `docs/requirements.md`:

| Requirement | Added | State |
|---|---|---|
| FR-ALERT-01-AC2 | A unit that is not assigned to an approved proposal (reserved and waiting, rejected, or assigned to another incident) is never notified: nothing recorded, the system says so, the assignment is untouched | testable now |
| FR-AUDIT-01-AC2 | Once a proposal is logged, changing its input data is refused and the original stays | testable now |
| FR-INFER-01-AC2 | With the network switched off, a report is still classified and proposed as normal | testable now |
| FR-SIM-01-AC2 | **A hypothesis**, marked as one: reports play back with their scenario gaps divided by a speed (60 s apart arrive 6 s apart at 10x, 10% tolerance) and the same scenario at the same speed repeats exactly. Confirmed or changed when the Scenario Reader is built | not testable: not built, stays a visible gap |
| FR-INFER-02-AC2 | Left blank on purpose, with the reason written in the requirement: it needs the real model on the target hardware | stays a visible gap |

The wording of the first three is the assistant's proposal that Ben approved; the numbers and the idea in the pace hypothesis are Ben's request. Ben to confirm the wording stands.

