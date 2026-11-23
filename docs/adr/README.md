# Architecture decision records

One file per decision that is expensive to reverse. A record says what was decided, what else was considered, and what a reader would not otherwise expect. The decider for all of them is Ben (Dranzer Rogue). Status is as written in each file.

| ADR | Decision | Date | Status |
|---|---|---|---|
| [0001](0001-choose-the-local-language-model.md) | Choose the local language model | 2026-09-27 | Accepted |
| [0002](0002-choose-the-data-store.md) | Choose the data store | 2026-09-27 | Accepted |
| [0003](0003-choose-the-simulation-framework.md) | Choose the simulation/agent framework | 2026-09-27 | Accepted |
| [0004](0004-choose-the-map-and-routing-representation.md) | Choose the map and routing representation for the MVP | 2026-09-27 | Accepted |
| [0005](0005-choose-the-project-license.md) | Choose the project license | 2026-09-27 | Accepted |
| [0006](0006-batch-mode-stand-in-approval-policy.md) | Batch-mode proposal decisions use a logged stand-in policy, not a real human | 2026-09-30 | Accepted |
| [0007](0007-information-richness-score.md) | Information richness is a documented score: distinct content words, plus two fixed bonuses | 2026-11-05 | Accepted |
| [0008](0008-two-factor-sign-in-with-time-based-codes.md) | Dispatcher sign-in: password plus a time-based code from the person's own phone | 2026-11-15 | DRAFT for Ben to confirm |
| [0009](0009-move-to-postgresql-behind-a-data-access-layer.md) | Move to PostgreSQL behind a data-access layer (MongoDB evaluated, not chosen) | 2026-11-18 | SUPERSEDED by ADR 0010 |
| [0010](0010-move-to-mongodb-behind-a-data-access-layer.md) | Move to MongoDB behind a data-access layer (supersedes ADR 0009) | 2026-11-18 | DRAFT for Ben to confirm |

## How to use this index
- **A decision changed?** Do not edit the old record's reasoning. Write a new ADR, mark the old one `SUPERSEDED by ADR NNNN` and link both ways (ADR 0009 was superseded by 0010 within a day, and its data-access-layer point still stands).
- **Drafts:** ADR 0008 and ADR 0010 are marked DRAFT because the assistant wrote them down from Ben's decisions; Ben confirms or edits them.
- **Not decided yet:** the move to MongoDB (ADR 0010) is a direction, not done; the app runs on SQLite today (backlog B-17).
- **Related documents:** requirements `docs/requirements.md`, change requests `docs/change-requests/`, defects `docs/defect-log.md`, the architecture overview `docs/architecture.md`.
