# Risk Register (draft)

Early draft of top risks, captured while scaling the concept in
`PROJECT.md`. This is a head start for the formal Risk Register due at
**Milestone 7** (Week 7, per `CALENDAR.md`) — treat it as a draft to be
formalized (likelihood/impact scoring, owner, status tracking) at that
point, not the final artifact.

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | Scope exceeds the 240-hour solo budget — Mesa + OSMnx real roads + LLM negotiation + 3 baselines (incl. MILP) + full test pyramid + CI + React/Leaflet dashboard + live demo, all stacked together | High | High | Strict weekly time-boxing against `CALENDAR.md` hour targets. Predefined cut order if behind: (1) drop MILP baseline, (2) drop fuzz/property tests, (3) fall back to synthetic grid map, (4) reduce scenario scale to small. |
| 2 | Local LLM (Ollama, small model) produces weak/inconsistent natural-language bids, undermining the core thesis comparison | Medium | High | Keep prompts tightly structured (still NL, but scaffolded). Validate early (weeks 2–3) with a throwaway negotiation prototype before locking architecture in the SDD (Milestone 6). |
| 3 | OSMnx/real-road-network setup (geocoding, routing, graph cleanup) eats unplanned hours | Medium | Medium | Throwaway **spike in weeks 5–6** (does the city graph load and route?) settles go/no-go while it's cheap; full integration is week 13. Fall back to a synthetic grid graph if the spike fails. Note the spike must respect Nominatim's 1 req/sec limit — geocode once and cache the graph to disk rather than re-fetching. |
| 4 | Local models are the *only* LLM option — paid/hosted APIs are out of scope by constraint, so weak local output can't be bought around | Medium | High | Validate quality early (weeks 2–3 prototype, per risk #2). If local output is too weak, respond by scaling scenarios down or moving to a stronger *local* model, not by adding a paid API. Keep the backend interface abstracted anyway so this stays a one-file change if the constraint ever lifts. |
| 5 | Live scenario demo fails during the final presentation (LLM latency spike, crash, flaky negotiation) | Medium | Medium | Demo script includes a pre-recorded run as a rehearsed fallback (rehearsal in week 15, per Milestone 15). |
| 6 | Demo map blanks out at the podium — OSM's tile policy forbids offline/bulk tile caching, so the live map depends on venue network | Medium | Medium | Build the dashboard's **tiles-free rendering mode** (road graph drawn directly as lines/markers, no basemap) and use *that* for the final demo. Removes the network dependency instead of mitigating it. |
