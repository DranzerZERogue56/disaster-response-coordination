# Spike SP-02 — Does SQLite lose or delay a unit reservation when two Mesa agent processes write at the same tick?

- **Unknown:** Whether SQLite's single-writer lock causes a lost, delayed, or duplicated unit reservation when multiple concurrent agent processes attempt to reserve the same unit at nearly the same instant.
- **Feeds:** ADR 0002 — data store (SQLite over PostgreSQL)
- **Requirements at risk:** FR-RES-03, FR-COORD-01
- **Time box:** 2 hours
- **Run on:** 2026-10-04

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

Ran against the real `migrations/0001-initial.sql` schema (not a toy table) — `spikes/sp-02-sqlite-write-contention.py`. For each of 20 trials, 3 separate OS processes raced the exact `UPDATE units SET status='reserved', reserved_by_proposal_id=? WHERE id=? AND status='available'` that the Resource/Unit Registry's `reserve()` interface (`docs/architecture.md` §5) is specified to run, each with its own real `agent_proposals` row so the foreign key constraints were exercised for real, not bypassed.

**20/20 trials clean.** Exactly one writer won every trial (`self_reported_wins` was always 1, never 0 or 2+), the row's final `status`/`reserved_by_proposal_id` always matched the actual winner, no trial hung past its 10-second join timeout, and no writer ever hit SQLite's busy-lock error at all — meaning contention at this scale (3 writers) never got severe enough to even exercise the retry/busy-timeout path. Max elapsed time for a full 3-way race was 0.026 seconds — several orders of magnitude under NFR-REL-02's 4-minute release window or any negotiation timeout in the design.

One early finding worth recording as the surprise: the first version of this script used literal writer IDs (1/2/3) for `reserved_by_proposal_id` and failed immediately with `FOREIGN KEY constraint failed` — the real schema's foreign key from `units.reserved_by_proposal_id` to `agent_proposals.id` caught a sloppy first draft of the spike itself before it ever got to test the actual question. Fixed by inserting a real `agent_proposals` row per writer. Minor, but a reminder that the schema's own constraints are doing real work, not just decoration.

**Caveat, stated plainly:** this ran on a development sandbox with no GPU and constrained memory, not the project's eventual target hardware. That doesn't weaken the result, though — this spike tests SQLite's write-locking behavior under OS-process contention, a property of SQLite and the operating system, not of GPU availability or model inference, so it should generalize to the real target machine unchanged.

## Decision

**Proceed with SQLite, no serialization layer added.** The failure criterion (any double-booking, any lost write, or risk of missing a timeout) never triggered across 20 trials. ADR 0002's revisit trigger — "if Spike SP-02 measures any lost or duplicated reservation" — did not fire, so ADR 0002 stands confirmed rather than superseded. The original tech-evaluation score for this criterion (3/5, "this is the seam Spike SP-02 exists to actually measure") is left as originally recorded in `docs/tech-evaluation.csv` rather than bumped after the fact to fit this result — that file is a dated Milestone 5 record, and retroactively improving a score because a later spike went well is exactly the kind of quiet thumb-on-the-scale the Milestone 5 assignment's own coaching note warned against. ADR 0002 gets a short, separate confirmation note instead (see below) — the right way to record new evidence against an old decision is to add to the record, not edit it.
