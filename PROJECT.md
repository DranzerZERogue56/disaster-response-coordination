# Adaptive Multi-Agent Disaster Response Coordinator

Senior capstone project. Solo, one semester, 240 hours total (see
`CALENDAR.md` for the week-by-week schedule and graded deliverables).
Focus areas: agentic AI, multi-agent orchestration, advanced software
architecture. No audio component and no real-world/adversarial
"manipulation" framing — this is a defensive/logistics coordination
system, entirely simulation-based.

## Problem

Simulate a large-scale disaster (earthquake, flood, mass-casualty event)
unfolding over a map. Incidents appear over time with location, severity,
type, and resource needs. Scarce resources (ambulances, fire units, shelter
capacity, medical supplies) must be allocated and continuously re-allocated
as the situation changes: new incidents spike, roads close, a hospital hits
capacity, a unit breaks down.

## Research question

Does natural-language agentic negotiation between resource agents outperform
classical auction/optimization-based multi-agent coordination when
disruptions require judgment calls that don't fit cleanly into a utility
function? Where does it lose (latency, cost, optimality on well-specified
subproblems)? This is the actual thesis — not "we built agents," but a
comparative claim about when agentic reasoning earns its complexity over
established MAS techniques.

## Architecture

Modeled loosely on FEMA's real Incident Command System (ICS) for credibility
and structure:

- **Resource agents** — one per resource category: **Medical, Fire,
  Shelter/Logistics, Security**. Each tracks its own pool: available units,
  locations, current commitments, ETAs.
- **Incident-command agent** — sets policy, not allocations (e.g. "life
  safety over property," "triage by severity," "protect zone B given storm
  forecast"). This is **LLM-reasoned**, not fixed rule-based: the command
  agent interprets evolving conditions in natural language and adjusts
  policy accordingly, matching the thesis that NL reasoning surfaces
  judgment calls a formula would miss. Resource agents negotiate within
  those constraints; command doesn't micromanage individual assignments.
- Decentralized negotiation, not a single allocation authority — more
  robust to single point of failure, and closer to how real agencies
  operate (no one has full authority over everyone else's trucks).

## Negotiation protocol

Classic **contract-net protocol** (announce → bid → award) as the
backbone, well established in MAS research, **hand-rolled** rather than
built on a heavy agent framework (AutoGen/LangGraph) — this demonstrates
understanding of the MAS mechanics directly rather than gluing an SDK
together, which matters for a capstone graded on architecture decisions.
The novel piece: agents bid in natural language via LLM reasoning instead
of a fixed utility function, so they can surface tradeoffs a formula would
miss — e.g. "I can cover this, but zone B goes uncovered for 10 minutes
given the storm forecast — acceptable?"

## Replanning under disruption

The main evaluated capability, not just initial allocation. Mid-scenario,
inject all three disruption types:

- **Road closure**
- **Unit failure/breakdown**
- **Incident surge**

Agents must renegotiate committed assignments quickly. Recovery speed and
quality after a disruption is where cascading failures happen in real
incidents, and where the system is actually tested.

## Tech stack (locked)

Everything below is free, open-source, and usable without creating any
account or API key — a hard constraint for this project (the only money
in scope is the optional local hardware in `HARDWARE.md`).

- **Simulation engine**: **Mesa 3.x** (Python agent-based modeling
  framework). Chosen over a hand-rolled tick loop or bare SimPy for its
  `AgentSet` API (filtering/grouping/activating heterogeneous agent
  populations), its scheduling model, and its `discrete_space` module —
  structure that fits "many autonomous agents on a shared environment"
  directly. Note: Mesa 3 moved visualization out to a separate
  Solara-based system (`SolaraViz`, still experimental) and no longer
  installs all dependencies by default — neither matters here, because
  the dashboard is React + Leaflet, not Mesa's own viz.
- **Map**: real road network via **OSMnx** (pulls an actual city's road
  graph from OpenStreetMap — no API key, no account). A throwaway
  **spike in weeks 5–6** answers "does the city graph load and route?"
  and settles the go/no-go; full integration lands in week 13. Fallback
  is a synthetic grid graph if the spike fails (see Risks).
- **LLM backend**: **Ollama** (local, OpenAI-compatible HTTP endpoint),
  free and account-free. All LLM calls go through **one abstraction
  interface** from week 2 onward — good architecture regardless, and it
  keeps a provider swap cheap — but **hosted/paid API backends
  (Anthropic, OpenAI, etc.) are explicitly out of scope for this
  project**: they cost money and require accounts, which this project's
  constraints forbid. If local models underperform, the response is
  smaller scenarios or a stronger local model, not a paid API.
- **Agent orchestration**: hand-rolled contract-net protocol (see above),
  not LangGraph/AutoGen.
- **Dashboard**: **React + Leaflet**, live map showing agents, incidents,
  and resource movement — strong for the live final demo. Basemap tiles
  come from OpenStreetMap (no API key), but OSM's tile usage policy
  forbids offline/bulk caching, so the dashboard also ships a
  **tiles-free rendering mode** that draws the road graph directly as
  lines/markers on a blank canvas. That mode is the one used for the
  final demo: it removes the podium-network dependency entirely.
- **Baselines** (see Evaluation): plain Python; MILP baseline via
  **PuLP**, which bundles the CBC solver and is a thin, easily-learned
  wrapper — deliberately chosen over OR-Tools, which is far more machine
  than a small ceiling-comparison baseline needs (and this baseline is
  first on the cut list anyway).

## Scope & scale

- **Scenario scale**: medium — roughly 30–50 incidents and 25–40 resource
  units per scenario. Large enough to feel like a real disaster and stress
  negotiation, small enough to stay debuggable on local LLM inference.
- **Resource categories**: all four (Medical, Fire, Shelter/Logistics,
  Security).
- **Disruption types**: all three (road closure, unit failure, incident
  surge).

## Evaluation

Baselines to implement:
- Greedy nearest-unit assignment
- Classical contract-net (no LLM, pure utility bidding)
- Small MILP/optimal solver (**PuLP**, bundled CBC) on reduced scenarios,
  as a ceiling comparison

Metrics: response time, % incidents served within SLA, resource
utilization, recovery time post-disruption, and **fairness across zones**
— operationalized as variance in %-within-SLA across zones (does one
zone/neighborhood systematically get worse service?).

**Evaluation rigor**: 5–10 runs per condition per scenario type, with
basic descriptive stats (mean/variance). This is framed as an exploratory
comparative study, not a large-n statistical claim — realistic for a solo
240-hour budget.

**Simulation pacing (two modes)**:
- The **evaluation harness** runs scenarios decoupled from wall-clock time
  (fast), which is what makes 5–10+ repetitions per condition practical.
- The **dashboard/demo mode** plays a run back at real-time pace (either
  live or a recorded run), since the final presentation's demo is a live
  scenario run on the dashboard.

## Reproducibility

A scripted setup (install deps, pull a specified small Ollama model) so a
grader can plausibly run this on a clean machine, per the Milestone 13
documentation requirement — and with no account signup or API key needed
anywhere in that path. LLM-dependent tests are mockable/stubbed so CI
doesn't require live inference.

## Testing

Full test pyramid, sized for solo 240-hour budget:
- Unit tests on core logic (bid scoring, contract award, disruption
  handling)
- Scenario-replay regression tests (fixed scenarios with expected
  outcomes)
- Property-based/fuzz tests on generated scenarios (e.g. invariant: no
  resource is ever double-booked)

## CI

GitHub Actions running the full test suite, including scenario-replay
tests. LLM-dependent paths must be mockable so CI doesn't require live
inference or incur API/inference cost on every push.

## Final presentation

Live scenario run on the dashboard during the presentation (accepted
risk: LLM latency or a crash mid-demo). A pre-recorded run is kept as a
rehearsed fallback in the demo script — not the primary plan, but a
safety net if the live run misbehaves.

## Scope discipline

This concept intentionally stacks several non-trivial pieces (Mesa +
OSMnx real roads + LLM negotiation + 3 baselines including MILP + full
test pyramid + CI + React/Leaflet dashboard + live demo) inside a solo
240-hour budget — see `RISKS.md` for the specific risk this creates. If
behind schedule, cut in this order:

1. Drop the MILP baseline (keep greedy + classical contract-net)
2. Drop property-based/fuzz tests (keep unit + scenario-replay)
3. Fall back from real OSMnx map to a synthetic grid graph — decided by
   the weeks 5–6 spike, not left to week 13
4. Reduce scenario scale from medium to small (~10–20 incidents)

## Rough scope (one semester, aligned to CALENDAR.md)

1. Scenario engine (Mesa) + incident generator + greedy baseline
2. Resource agents + contract-net negotiation (LLM-based bidding via
   Ollama, behind a swappable backend interface)
3. Incident-command LLM policy layer + disruption injection + replanning
4. Classical contract-net and MILP baselines
5. Evaluation harness across scenario runs vs. baselines; fairness metric
6. Full test pyramid + CI
7. Dashboard (React + Leaflet) + real road network (OSMnx)
8. Writeup, documentation set, clean-machine reproducibility script
9. Stress-test larger scenarios, presentation deck, demo rehearsal

## Status

Concept scaled and locked to fit the 16-week/240-hour solo calendar. No
code yet.
