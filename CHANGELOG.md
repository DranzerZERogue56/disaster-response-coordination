## Specification changes since baseline v1.0

Baseline declared 2026-10-18 (`docs/baseline.md`). No change requests have been raised since — this table is empty by design, not by omission; it starts filling the first time something crosses the threshold rule below.

| CR | Date | Change | Requirements | Hours | Decision |
|---|---|---|---|---:|---|
| CR-001 | 2026-11-01 | Database triggers: a unit is `assigned` only while its proposal is `approved`/`modified` (migration 0002) | FR-AGENT-03, NFR-SEC-02, FR-RES-01 | +0.5 | approved |
| CR-002 | 2026-11-01 | Override follow-ups become an append-only table; override rows can no longer be edited (migration 0003) | FR-RES-02, FR-AUDIT-02 | +0.5 | approved |
| CR-003 | 2026-11-05 | Acceptance criteria written for FR-ALERT-01, FR-AUDIT-01, FR-AUDIT-02, FR-SIM-01, FR-INFER-01, FR-INFER-02; "[X] seconds" set to 10 (FR-ALERT-01) and 5 (FR-INFER-02) | those six | +0.5 | approved |
| CR-004 | 2026-11-05 | Proposals record the input data the agent used (`agent_proposals.input_data`, final once written; migration 0004) | FR-AUDIT-01 | +0.5 | approved |
| CR-005 | 2026-11-05 | NFR-SEC-03: synthetic reports live in `tests/data/` and `seed/` (not `data/synthetic/`); check script `tools/check_synthetic.py` | NFR-SEC-03 | +0.5 | approved |
| CR-009 | 2026-11-05 | Purge Job: units are reset not deleted, nodes untouched; success shape lists purged and reset tables (NFR-PRIV-01) | NFR-PRIV-01 | +0.25 | approved |

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
