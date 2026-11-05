# CR-010 — Unit status changes are published to every other agent (migration 0008)

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, data model (`docs/architecture.md` section 6) |
| Trigger | Milestone 11 work plan, Task 14 (FR-RES-03 acceptance criteria 1 to 3). The requirement says every agent sees a unit's status change, an update that cannot be delivered is cached or warned about, and a reservation is timestamped and sent to the other agents so their decisions exclude that unit. The registry holds one status per unit and has no way to tell the other agents |

## What changes
Adds two tables and one trigger in `migrations/0008-unit-status-broadcast.sql`; nothing existing changes.

- **`unit_events`**: the history of unit status changes: unit, new status, the proposal involved, the reservation timestamp (`at`) and the real time it was written (`recorded_at`).
- **`agent_inboxes`**: one row per event and receiving agent node. Delivered at once to a node that is alive or recovered; **cached** (`delivered_at` empty) for a node that is `not_responding`. A unit's own agent node is the source of its changes and gets no inbox row for them.
- **Trigger `units_status_published`** on `units`: every status change, from any writer, writes the event, the inbox rows, and a warning notice (`node_notices`) to each reachable agent for every node the update could not be delivered to. It was made a trigger because the registry, decide, override, tiebreak and purge all write `units.status`; a rule that holds only for callers who remember it is not a rule.

`src/unit_registry/broadcast.py` reads the result: `agent_view` (one agent's picture of every unit), `choices` (the units that agent sees as available, which is how a reservation excludes the unit from other agents' choices) and `deliver_cached` (called by the heartbeat when a node responds again, so cached updates arrive in event order).

The purge job deletes events and inboxes older than 24 hours or belonging to purged proposals.

## Why
Without it each agent decides from its own picture and two agents can propose the same unit. The cache and warning mean a node that was down is not silently left with a stale picture.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-RES-03 (criteria 1 to 3 now verifiable; criterion 4 was already tested); NFR-PRIV-01 (purge extended) |
| Specification sections affected | `docs/architecture.md` section 6 (two new entities) |
| Hours: added / removed | +0.75 / -0 |
| Schedule effect | none |
| Risk effect | lowers the risk of agents acting on a stale unit picture; adds a trigger that fires on every status change (negligible at this scale) |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-05 |
| Rationale | Stretch Task 14 of the work plan Ben approved ("lets go native"); built as insurance because the 90% target otherwise depends on one manual keyboard pass |

## Applied

- [x] Specification updated and committed (this CR and the migration)
- [x] Traceability matrix: FR-RES-03 criteria 1 to 3 now have tests
- [x] Plan and hours re-baselined: not needed
- [x] Row added to `CHANGELOG.md`
- [ ] New baseline tag: Ben to decide
