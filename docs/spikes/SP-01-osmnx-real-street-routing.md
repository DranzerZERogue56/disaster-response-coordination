# Spike SP-01 — Does OSMnx produce a usable, routable street graph for the demo's target town?

- **Unknown:** Whether OSMnx can pull a real street graph for the capstone demo's target town and actually compute a route between two real places in it.
- **Feeds:** ADR 0004 — map/routing representation for the MVP
- **Requirements at risk:** FR-MAP-01
- **Time box:** 30 minutes (reconstructed — see disclosure)
- **Run on:** 2026-09-06

## Disclosure

This spike was run on 2026-09-06 during early idea exploration, before this milestone's spike-plan template existed, so it wasn't written down as a formal time-boxed plan in advance. The question, success/failure criteria, and time box below are reconstructed now from the actual session transcript (timestamped requests and responses), not invented after the fact to flatter the result — the Result section below reports what actually happened, including the part that didn't work. The real elapsed time, read off the transcript timestamps (first attempt requested 20:19, final result recorded 20:24), was about 5 minutes, comfortably inside the reconstructed 30-minute box. `SP-02` and `SP-03` are planned in advance, per the template, since this one wasn't.

## The question

Does OSMnx build a usable, routable street graph for Macomb, IL (the demo's target town), and can at least one realistic pair of named places in it produce a real route?

## The smallest thing that answers it

Install OSMnx, pull the Macomb, IL street graph with `osmnx.graph_from_place`, and attempt to geocode and route between two named business locations.

## Success criterion

The graph builds without error, and at least one of the two attempted location pairs returns a route with a plausible distance.

## Failure criterion

The graph fails to build, or no attempted location pair anywhere returns a route.

## Plan B if it fails

Fall back to a synthetic, hand-authored location graph instead of real street data for the MVP — which is, in fact, the option ADR 0004 chose anyway, for a separate reason this spike didn't test (novelty load and offline reliability, not routing correctness).

## Result

The road graph itself built successfully: 641 nodes, 1,804 edges, in 7.3 seconds — Macomb's OSM road data is solid and routable. The first attempt, Taco Bell to Dad's Garage, failed at the geocoding step, not the routing step: Nominatim's geocoder wants structured street addresses, not bare business names, and no "Taco Bell" was tagged in OpenStreetMap for Macomb at all — a data-coverage gap, not a library bug. The second attempt, McDonald's to Chick-fil-A, succeeded end to end: the cached graph reloaded in 1.2 seconds, the route computed in 8 milliseconds, and the result was a real, sane distance (2.12 miles). Surprise finding: raw business names are not a reliable input to OSMnx's geocoder — a real deployment would need either structured addresses from the incident report, or a separate name-to-coordinate resolution step before handing anything to OSMnx.

## Decision

**Proceed (Get-gate pass), with an unbudgeted cost now on the record.** The core technical question — can this library route real places in the demo town — is answered yes. But the spike also surfaced a real integration cost that isn't just "learn a new library": resolving a business name or informal location description to something OSMnx can geocode is its own small feature, not covered by this spike or by the current requirements. That cost is part of what ADR 0004 weighs when it defers full OSMnx integration past the MVP — the honest total isn't just the library's learning curve, it's the library's learning curve plus a geocoding-input problem this spike exposed but didn't solve.
