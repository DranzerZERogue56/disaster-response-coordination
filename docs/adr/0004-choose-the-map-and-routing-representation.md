# ADR 0004 — Choose the map and routing representation for the MVP

- **Status:** Accepted
- **Date:** 2026-09-27
- **Decider:** Dranzer Rogue
- **Requirements affected:** FR-MAP-01, NFR-REL-03, NFR-REL-04, NFR-MNT-01
- **Related ADRs:** 0003 (this is the novelty-load demotion that keeps Mesa's learning curve affordable); superseding this ADR would reopen the seam row in `docs/tech-evaluation.md` currently rated Low

## Context

FR-MAP-01 requires displaying the boundary of an active incident zone on the operator dashboard, updated whenever the zone is redefined. The obvious, most realistic way to satisfy this is OSMnx, a library that pulls a real OpenStreetMap street graph and computes real routes and distances — and this was in fact spiked successfully back on 2026-09-06 (Spike SP-01), returning real routes for two test address pairs in Macomb, IL.

But this milestone's novelty-load count came up short before this decision even reached the matrix: local Ollama serving and the hand-rolled contract-net protocol (ADR 0001) are new, and Mesa (ADR 0003) is also new. That's already 3 new things to learn simultaneously inside a 240-hour solo budget, and OSMnx would make it 4 — a real geospatial library with its own concepts (graph projection, nearest-node snapping, Overpass API rate limits) layered on top of everything else. NFR-REL-03 and NFR-REL-04 also matter here directly: the system has to survive a simulated 2-minute and 20-minute network outage with 0% and ≤2% report loss respectively, and OSMnx's first graph pull is a network call to the Overpass API — a live dependency sitting exactly inside the window those two requirements are testing.

Two real options were evaluated: OSMnx (the real-street graph, already spiked and working) and a synthetic location graph (a small hand-authored set of named locations and a fixed distance table, no external library or network call).

## Options considered

| Option | Weighted score | The detail that decided it |
|---|---:|---|
| synthetic location graph | 3.95 | No new library, no network dependency, ships in under an hour, and matches the synthetic-only demo data NFR-SEC-03 already requires — the cost is lower realism against FR-MAP-01 |
| OSMnx real-street graph | 3.45 | Best fit for FR-MAP-01's literal "real dashboard" framing, and already proven to work (Spike SP-01) — the cost is a fourth simultaneous new technology and an untested network seam against the outage requirements |

## Decision

We will use a **synthetic location graph** (hand-authored named locations and a fixed distance table, no external mapping library) for the MVP, demoting OSMnx to a deferred upgrade. Unlike ADR 0002, this is not an override of the matrix — the matrix's own top score (3.95 vs. 3.45) already favors the synthetic graph, because the "hours to first working version / novelty load" criterion was deliberately weighted at 0.30, the heaviest weight in this decision. That weight reflects a real constraint (a fixed 240-hour solo budget with three other new technologies already committed this milestone), not a preference for the easier option — the alternative honestly considered was weighting realism (FR-MAP-01 fit) heaviest instead, which would have flipped the result toward OSMnx.

This keeps the project's total novelty load at 3 new things (Ollama/local serving, Mesa, the hand-rolled contract-net protocol) instead of 4, per the demotion decision recorded in `docs/tech-evaluation.md`.

## Consequences

**Positive**

- No new library, no Overpass API dependency, no network call anywhere in the map/routing path — trivially clears the NFR-REL-03/NFR-REL-04 outage simulations.
- Ships fast (under an hour), freeing hours for the Mesa and contract-net learning curves that matter more to the capstone's actual thesis (competing negotiating agents), rather than to how the map is rendered.

**Negative**

- Weaker fit to FR-MAP-01's literal framing — a hand-authored distance table is not "the boundary of an active incident zone" on a real street map, and a design reviewer in Week 8 may reasonably ask why the dashboard doesn't show real geography. Mitigation: none needed for the MVP defense, since NFR-SEC-03 already requires synthetic-only demo data anyway, so a synthetic map is consistent with a synthetic scenario. Cost of upgrading later: the already-completed Spike SP-01 means OSMnx integration is de-risked technically; budgeting ~4-6 hours to re-integrate it once Mesa and the contract-net protocol are stable is realistic.
- Loses the demonstrated value of Spike SP-01 for this milestone specifically — the spike proved OSMnx works, but that proof isn't being used yet. This is intentional: proving something works and having the hours to integrate it under everything else happening this week are two different questions.

## Revisit trigger

Revisit this ADR (write a superseding ADR, do not edit this one) if, by the Milestone 9 walking-skeleton checkpoint (Week 9), the Mesa scheduler and the contract-net negotiation protocol are both stable with at least 20 hours of budget remaining before Week 12 — at that point, re-integrate OSMnx using the already-validated Spike SP-01 approach.

## Verification

| Claim in this ADR | Source | Checked on |
|---|---|---|
| OSMnx license: MIT | https://github.com/gboeing/osmnx/blob/main/LICENSE.txt | 2026-09-27 |
