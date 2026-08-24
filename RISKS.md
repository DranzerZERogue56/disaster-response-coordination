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
| 3 | OSMnx/real-road-network setup (geocoding, routing, graph cleanup) eats unplanned hours | Medium | Medium | Time-box to the design phase (weeks 5–6, aligned with Milestones 5–6). Fall back to a synthetic grid graph if not working by end of week 6. |
| 4 | Switching LLM backend mid-semester (Ollama → Claude API) changes latency/cost assumptions after evaluation code is already written | Low | Medium | Abstract all LLM calls behind one interface starting week 2, so a backend swap is a config change, not a rewrite of negotiation/eval logic. |
| 5 | Live scenario demo fails during the final presentation (LLM latency spike, crash, flaky negotiation) | Medium | Medium | Demo script includes a pre-recorded run as a rehearsed fallback (rehearsal in week 15, per Milestone 15). |
