## Specification changes since baseline v1.0

Baseline declared 2026-10-18 (`docs/baseline.md`). No change requests have been raised since — this table is empty by design, not by omission; it starts filling the first time something crosses the threshold rule below.

| CR | Date | Change | Requirements | Hours | Decision |
|---|---|---|---|---:|---|
| CR-001 | 2026-11-01 | Database triggers: a unit is `assigned` only while its proposal is `approved`/`modified` (migration 0002) | FR-AGENT-03, NFR-SEC-02, FR-RES-01 | +0.5 | approved |
| CR-002 | 2026-11-01 | Override follow-ups become an append-only table; override rows can no longer be edited (migration 0003) | FR-RES-02, FR-AUDIT-02 | +0.5 | approved |

### The threshold rule — when a change needs a CR

Raise a change request (`docs/change-requests/CR-000-template.md`) if the change does any of these:

1. Adds, removes, or materially rewords a **Must** requirement.
2. Changes an **interface contract** or the **data model**.
3. Moves a **milestone date** or changes the total plan by more than **4 hours**.
4. Changes the **stack** — a new language, framework, database, or hosting provider.
5. Changes the **definition of done**.

Everything else — typos, clarifications that don't change meaning, formatting, added examples — is an ordinary commit with a clear message.

---

This project has no code-level releases yet (construction starts Milestone 9); this file tracks specification changes only until then.
