# CR-007 — Incident versions and a reconciliation log (migration 0007)

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, data model (`docs/architecture.md` section 6) |
| Trigger | Milestone 11 work plan, Task 6 (FR-COORD-02). Two agents can hold different, differently-timestamped pictures of one incident; the newer must become active, the older must be kept, and a human override must be logged with who, when, why and the original automatic decision. The data model holds one picture per report and nowhere to keep history or log a reconciliation |

## What changes
Adds two tables in `migrations/0007-incident-versions.sql`; nothing existing changes.

- **`incident_versions`**: one row per agent picture (report, agent node, data, data time, active flag, recorded and superseded times). A unique partial index allows at most one active version per incident. A trigger refuses edits to what a version says; only `active` and `superseded_at` change. Rows are removed only by the 24-hour purge.
- **`reconciliation_log`** (append-only; a trigger refuses edits): the kind (`automatic` or `override`), the original automatic decision, the chosen version, who decided and why (both mandatory for an override, enforced by CHECK constraints), and when.

Rule: the newest data time wins; equal data times go to the version recorded later, so the result is deterministic. A human override stands until newer data changes the automatic choice. The purge job deletes both tables' rows for purged reports.

New route: `POST /reconciliations/<report_id>/override` with `{version_id, reason}`; the dispatcher is the stand-in account, as for the other human actions.

## Why
Silently overwriting one agent's picture with another's loses evidence, and an override nobody can trace cannot be audited. History plus a log makes both visible.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-COORD-02 (now verifiable); NFR-PRIV-01 (purge extended) |
| Specification sections affected | `docs/architecture.md` section 6 (two new entities) |
| Hours: added / removed | +0.5 / -0 |
| Schedule effect | none |
| Risk effect | lowers the risk of lost or untraceable incident data |
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
- [x] Traceability matrix: FR-COORD-02 criteria now have tests
- [x] Plan and hours re-baselined: not needed
- [x] Row added to `CHANGELOG.md`
- [ ] New baseline tag: Ben to decide
