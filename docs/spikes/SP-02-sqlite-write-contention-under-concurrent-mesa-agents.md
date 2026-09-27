# Spike SP-02 — Does SQLite lose or delay a unit reservation when two Mesa agent processes write at the same tick?

- **Unknown:** Whether SQLite's single-writer lock causes a lost, delayed, or duplicated unit reservation when multiple concurrent agent processes attempt to reserve the same unit at nearly the same instant.
- **Feeds:** ADR 0002 — data store (SQLite over PostgreSQL)
- **Requirements at risk:** FR-RES-03, FR-COORD-01
- **Time box:** 2 hours
- **Run on:** not yet run — planned for this week, before the Milestone 5 resubmission

## The question

When 3 concurrent agent processes each attempt to reserve the same unit within the same simulated tick, does SQLite's write lock ever cause a reservation write to be lost, silently overwritten, or delayed past the point where FR-COORD-01's tiebreak can still apply correctly — across 20 trials?

## The smallest thing that answers it

A standalone script, no Mesa and no UI: spin up 3 processes (or threads issuing separate connections) that all attempt an `UPDATE units SET status='reserved' WHERE id=? AND status='available'` against the same row at the same moment, 20 times. Log which process's write actually lands each trial, and whether any trial produces more than one "success," or a write that silently disappears.

## Success criterion

Across 20 trials, exactly one writer succeeds per trial, no trial produces two "successful" reservations for the same unit, and no write is lost (every trial has exactly one winner, verified by re-reading the row after all 3 attempts finish).

## Failure criterion

Any trial where more than one writer reports success for the same unit, or where a trial ends with no writer's reservation reflected in the row (a lost write), or where a single write takes long enough to risk missing FR-COORD-04's consensus timeout.

## Plan B if it fails

Add a serialization layer in the application (a single-writer queue in front of the reservation table) rather than switching data stores outright — this was already budgeted in ADR 0002 at roughly 4 hours. Escalating to PostgreSQL is the fallback behind that fallback, budgeted at roughly 8 hours including a new backup/restore runbook.

## Result

*(to fill in after the spike runs)*

## Decision

*(to fill in after the spike runs)*
