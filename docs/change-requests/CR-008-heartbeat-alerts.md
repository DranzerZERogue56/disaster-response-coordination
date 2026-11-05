# CR-008 — Node-failure alerts and notices (migration 0005)

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, data model (`docs/architecture.md` section 6) |
| Trigger | Milestone 11 work plan, Task 8 (FR-DEGRADE-01, NFR-REL-01). The requirement says a stopped node is detected within 30 seconds, the other agents and a human are notified, a late recovery is shown on the earlier notices, and a human checks that nothing was affected. `agent_nodes` has a status but nowhere to record an episode or a notice |

## What changes
Adds two tables in `migrations/0005-heartbeat-alerts.sql` (numbered 0005 because that number was free; the runner applies by version and the tables depend on nothing in 0006 or 0007); nothing existing changes.

- **`node_alerts`**: one row per episode: the node, when it was flagged, how long it had been silent, when it resumed (`recovered_at`), and which dispatcher confirmed and when. CHECK constraints: a confirmation needs both a time and a dispatcher, and cannot happen before the node has resumed.
- **`node_notices`**: one row per notice: audience `agent` (one for each other node still alive) or `human`, the message, and a `late_recovery` flag with an update time that is set when the node resumes.

Rules (all in `src/heartbeat/service.py`): flagged after `interval_s * misses` = 10 s x 3 = 30 s of silence; polling is idempotent; the node becomes `recovered` only through `confirm_recovery` by a dispatcher (the existing `agent_nodes` CHECK already forbids `recovered` without one); a node that resumed and goes quiet again before confirmation raises a new alert.

New routes: `POST /nodes/<id>/heartbeat`, `POST /nodes/<id>/confirm-recovery` (stand-in dispatcher), `GET /alerts`. The background watcher starts only when `HEARTBEAT_CHECK_SECONDS` is set, because nothing in the demo sends heartbeats and the seeded node would be flagged at once.

These tables hold node health, not incident data, so the 24-hour purge leaves them alone.

## Why
A node that dies silently leaves every other agent with a stale picture and nobody knows. An alert that is not recorded, or a node that is quietly trusted again without a person looking, is the failure this requirement exists to prevent.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | FR-DEGRADE-01 (now verifiable); NFR-REL-01 (Task 9 measures real processes) |
| Specification sections affected | `docs/architecture.md` section 6 (two new entities) |
| Hours: added / removed | +0.5 / -0 |
| Schedule effect | none |
| Risk effect | lowers the risk of a silent node failure |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-05 |
| Rationale | Part of the work plan Ben approved ("lets go native"); decision D6 (late recovery marked at once, `recovered` only after a human confirms) |

## Applied

- [x] Specification updated and committed (this CR and the migration)
- [x] Traceability matrix: FR-DEGRADE-01 criteria now have tests
- [x] Plan and hours re-baselined: not needed
- [x] Row added to `CHANGELOG.md`
- [ ] New baseline tag: Ben to decide
