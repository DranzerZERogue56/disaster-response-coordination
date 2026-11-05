# CR-004 — Each proposal records the input data the agent used (migration 0004)

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, data model (`docs/architecture.md` section 6) |
| Trigger | Milestone 11 acceptance test `test_FR_AUDIT_01_AC1_...` failed (defect DEF-014). FR-AUDIT-01 says every proposal is logged "including what data it used and its confidence score"; the log recorded the confidence and reasoning but not the data, only a `report_id` pointing at a row that can be purged after 24 hours. Ben's criterion (CR-003): "It should include input data." |

## What changes
Adds `agent_proposals.input_data` (JSON text, nullable) and one trigger that refuses any change to it once written (migration `migrations/0004-proposal-input-data.sql`). Classify & Propose writes the snapshot of the report fields the agent read, at the moment the proposal is generated.

Before: a proposal row had `confidence`, `reasoning`, `alternatives`, `model_identifier`, but nothing that preserved the input.
After: the same row also holds `input_data`, so the log entry is self-contained and its input cannot be altered afterwards.

## Why
FR-AUDIT-01 exists so a reviewer can see the agent's real reasoning, not just the outcome. A log that points at data which may change or be purged cannot show that. Existing rows stay valid (the column is nullable) and no existing behaviour changes.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-AUDIT-01 (now verifiable), NFR-PRIV-01 (the snapshot is personal-data-free in this release: synthetic reports only; when real data exists the purge job must delete `input_data` along with the proposal, which it does as it deletes the whole row) |
| Specification sections affected | `docs/architecture.md` section 6 (Agent Proposal entity) |
| Hours: added / removed | +0.5 / -0 |
| Schedule effect | none |
| Risk effect | lowers the chance of an unexplainable audit log; adds a small amount of stored text per proposal |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-05 |
| Rationale | Ben wrote the criterion that exposed the gap and chose to meet it. Small, additive, nullable column. Self-approved; no Must requirement wording changed |

## Applied

- [x] Specification updated and committed (this CR, invariant note in `docs/architecture.md`)
- [x] Traceability matrix: FR-AUDIT-01-AC1 now has a passing test
- [x] Plan and hours re-baselined: not needed (+0.5 h)
- [x] Row added to `CHANGELOG.md`
- [x] New baseline tag: not needed
