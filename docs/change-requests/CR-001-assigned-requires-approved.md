# CR-001 — Database enforces: a unit is "assigned" only while its proposal is approved

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-01 |
| Date raised | 2026-11-01 |
| Baseline affected | spec-baseline-v1.0 (data model, `docs/architecture.md` §6) |
| Trigger | Milestone 10 self-review finding 3.2: assigning a unit and approving its proposal were two separate saves. Ben's instruction: "make it hard-coded: if it's assigned it's approved." The application fix (one transaction) shipped in `068c3ef`; Ben then asked for database-level enforcement so no writer can break the rule |

## What changes
Adds migration `migrations/0002-assigned-requires-approved.sql` with three triggers. No table or column changes.

Before: nothing in the schema stopped a unit from being `assigned` while its proposal was undecided or rejected. Only application code upheld it.

After:
1. A unit cannot be inserted or updated to `assigned` unless the proposal it references (`reserved_by_proposal_id`) has `final_status` `approved` or `modified`.
2. A proposal cannot move away from `approved`/`modified` (to `rejected` or back to undecided) while a unit is assigned to it.

`modified` is allowed alongside `approved` because a dispatcher override (FR-RES-02, Milestone 10 slice 7) is an approval with a different unit.

## Why
A unit marked assigned for a proposal nobody approved is a dispatch without human or rule sign-off, which is exactly what NFR-SEC-02 forbids. A code-only guarantee holds until the next module, hand-typed fix or bug skips it. This makes the guarantee a property of the data.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-AGENT-03, NFR-SEC-02, FR-RES-01 (strengthened, none reworded) |
| Specification sections affected | `docs/architecture.md` §6, Resource/Unit Registry and Agent Proposal invariants (add invariant I-assigned) |
| Hours: added / removed | +0.5 / -0 (already spent) |
| Schedule effect | none |
| Risk effect | lowers the chance of a silent unsafe dispatch; adds one way for a bad write to fail loudly (intended) |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-01 |
| Rationale | Ben asked for it directly ("I do want the database-level enforcement"). Small, additive, no data migration, and it makes the safety rule independent of the code that currently follows it. Self-approved; no Must requirement text changed, so no new baseline tag |

## Applied

- [x] Specification updated and committed (this CR plus the invariant note in `docs/architecture.md`)
- [x] Traceability matrix: not needed (no new requirement)
- [x] Plan and hours re-baselined: not needed (+0.5 h, under the 4 h threshold)
- [x] Row added to `CHANGELOG.md`
- [x] New baseline tag: not needed (no Must requirement changed)
