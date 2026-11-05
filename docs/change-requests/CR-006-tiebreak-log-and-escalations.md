# CR-006 — A tiebreak log and a human-escalation queue (migration 0006)

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, data model (`docs/architecture.md` section 6) |
| Trigger | Milestone 11 work plan, Task 5 (FR-COORD-01 and FR-COORD-03). FR-COORD-01-AC1 requires the resolution to be "logged as having followed the correct protocol", and AC2 requires the losing agent's incident to find the next best unit "instead of leaving the incident unassigned". The data model has no place to log a resolution, and no place to put an incident that cannot be placed |

## What changes
Adds two tables in `migrations/0006-tiebreak-log-and-escalations.sql`; nothing existing changes.

- **`tiebreak_log`** (append-only; a trigger refuses edits): one row per resolved pair: winner, loser, the reason (`severity`, `richness`, `reported-first` or `true-tie`), both richness scores (so a stranger can recompute the result from ADR 0007), `protocol_followed`, and the time. A unique pair means resolving the same two proposals again returns the logged answer, not a second row.
- **`human_escalations`**: an incident that the system cannot place and a person must: the report, the proposal, the reason, and when it was raised and (later) resolved and by whom. It is written when a proposal that lost a tiebreak finds no other available unit, and (Task 10) when the whole model fallback chain fails.

The purge job (NFR-PRIV-01) also deletes both tables' rows for purged proposals and reports.

## Why
A tiebreak that is not logged cannot be audited, and an incident that loses a unit and is then forgotten is the worst outcome of a negotiation system. Both tables make the rule's effects visible and checkable.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-COORD-01, FR-COORD-03 (now verifiable); FR-DEGRADE-02 (Task 10 reuses the escalation table); NFR-PRIV-01 (purge extended) |
| Specification sections affected | `docs/architecture.md` section 6 (two new entities) |
| Hours: added / removed | +0.5 / -0 |
| Schedule effect | none |
| Risk effect | lowers the risk of a silently dropped incident |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-05 |
| Rationale | Part of the work plan Ben approved ("lets go native"). Additive tables, no existing behaviour removed |

## Applied

- [x] Specification updated and committed (this CR and the migration)
- [x] Traceability matrix: FR-COORD-01 and FR-COORD-03 criteria now have tests
- [x] Plan and hours re-baselined: not needed
- [x] Row added to `CHANGELOG.md`
- [ ] New baseline tag: Ben to decide
