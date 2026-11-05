# CR-009 — The purge resets units instead of deleting them, and leaves nodes alone

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, `docs/architecture.md` section 5 (Purge Job interface) |
| Trigger | Building the purge job (Milestone 11 work plan, Task 3). The Purge Job contract says it deletes rows "for overrides/units/nodes/notifications" and returns `units` and `agent_nodes` counts. Taken literally, that deletes the resources themselves 24 hours after a run's reports arrive and leaves the system with no units. Ben chose (decision D2) to reset units, not delete them |

## What changes
Before: the Purge Job hard-deletes units and agent nodes along with the incident data, and reports `purged: {incident_reports, agent_proposals, dispatcher_overrides, units, agent_nodes, notifications}`.

After: the job hard-deletes incident reports, proposals, overrides, override follow-ups and notifications older than the retention window; units that were held by a purged proposal are **reset to available** (reported under `reset: {units}`); agent nodes are not touched; `dispatcher_accounts` and `scenario_runs` are untouched, as before. The rule that a row whose parent is purged goes with it (so no row points at a deleted one) is added. The success shape becomes `{purged: {...}, reset: {units}, run_at}`.

## Why
NFR-PRIV-01 is about incident data and the decision and override audit trail ("stored incident-report data, including the decision and override audit trail, is purged 24 hours after receipt"). Units and nodes are the resources and configuration of the system, not incident data. Deleting them would break the system and would satisfy no part of the requirement. Resetting a unit after its proposal is gone removes the link to the purged incident, which is the privacy-relevant part.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | NFR-PRIV-01 (the measure is unchanged and still passes: zero rows for the seeded report ids in every data store) |
| Specification sections affected | `docs/architecture.md` Purge Job (a note on the Side effects line); the entity lifecycles for units and nodes still say "purged with the run's data" and are now superseded by this CR |
| Hours: added / removed | +0.25 / -0 |
| Schedule effect | none |
| Risk effect | removes the risk of an hourly job emptying the unit table |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-05 |
| Rationale | Ben said yes to resetting units (D2). The requirement's own wording covers incident data, not resources |

## Applied

- [x] Specification updated and committed (architecture note)
- [x] Traceability matrix: NFR-PRIV-01-AC1 has passing tests
- [x] Plan and hours re-baselined: not needed
- [x] Row added to `CHANGELOG.md`
- [ ] New baseline tag: Ben to decide
