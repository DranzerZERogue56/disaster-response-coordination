# CR-002 — Override follow-ups are an append-only table

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-01 |
| Date raised | 2026-11-01 |
| Baseline affected | spec-baseline-v1.0 (data model, `docs/architecture.md` §6) |
| Trigger | Milestone 10 self-review finding 7.2: the override follow-up edited the same row, so the override log could be rewritten. Ben's decision in the question round: "fix now with a separate follow-ups table" |

## What changes
Adds migration `migrations/0003-override-follow-ups.sql`: a new table `override_follow_ups` (one row per follow-up: which override, which dispatcher, the text, when) and two triggers that refuse any UPDATE of `override_follow_ups` or `dispatcher_overrides`.

Before: `dispatcher_overrides.follow_up_explanation` was a single text column that a follow-up appended to by editing the row.

After: each follow-up is a new row. The old column is left in place, unused and empty, so no existing data or contract changes. The log can be added to, not rewritten. Rows can still be deleted, because the 24-hour purge job (NFR-PRIV-01) must be able to.

## Why
FR-RES-02 says the follow-up is "added to the same log entry". Showing the entry together with its follow-ups satisfies that, and an audit log that anyone can quietly edit is not an audit log (FR-AUDIT-02, T-6.1 asks for append-only for proposals).

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-RES-02, FR-AUDIT-02 (strengthened, none reworded) |
| Specification sections affected | `docs/architecture.md` §6 (new entity, dispatcher_overrides invariant) |
| Hours: added / removed | +0.5 / -0 |
| Schedule effect | none (pulled forward from Milestone 12) |
| Risk effect | lowers the chance of an altered audit trail |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-01 |
| Rationale | Ben chose it. Small and additive; the old column stays so nothing breaks. Self-approved; no Must requirement text changed, so no new baseline tag |

## Applied

- [x] Specification updated and committed (this CR plus the note in `docs/architecture.md`)
- [x] Traceability matrix: not needed
- [x] Plan and hours re-baselined: not needed (+0.5 h, under the 4 h threshold)
- [x] Row added to `CHANGELOG.md`
- [x] New baseline tag: not needed
