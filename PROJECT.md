# Adaptive Multi-Agent Disaster Response Coordinator

Senior capstone project. Focus areas: agentic AI, multi-agent orchestration,
advanced software architecture. No audio component (dropped from earlier
scoping) and no real-world/adversarial "manipulation" framing (also dropped) -
this is a defensive/logistics coordination system, entirely simulation-based.

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
subproblems)? This is the actual thesis - not "we built agents," but a
comparative claim about when agentic reasoning earns its complexity over
established MAS techniques.

## Architecture

Modeled loosely on FEMA's real Incident Command System (ICS) for credibility
and structure:

- **Resource agents** - one per resource category (Medical, Fire,
  Shelter/Logistics, Security). Each tracks its own pool: available units,
  locations, current commitments, ETAs.
- **Incident-command agent** - sets policy, not allocations (e.g. "life
  safety over property," "triage by severity," "protect zone B given storm
  forecast"). Resource agents negotiate within those constraints; command
  doesn't micromanage individual assignments.
- Decentralized negotiation, not a single allocation authority - more
  robust to single point of failure, and closer to how real agencies
  operate (no one has full authority over everyone else's trucks).

## Negotiation protocol

Classic **contract-net protocol** (announce -> bid -> award) as the
backbone, well established in MAS research. The novel piece: agents bid in
natural language via LLM reasoning instead of a fixed utility function, so
they can surface tradeoffs a formula would miss - e.g. "I can cover this,
but zone B goes uncovered for 10 minutes given the storm forecast -
acceptable?"

## Replanning under disruption

The main evaluated capability, not just initial allocation. Mid-scenario,
inject disruptions: road closure, unit failure, incident surge. Agents must
renegotiate committed assignments quickly. Recovery speed and quality after
a disruption is where cascading failures happen in real incidents, and
where the system is actually tested.

## Evaluation

Baselines to implement:
- Greedy nearest-unit assignment
- Classical contract-net (no LLM, pure utility bidding)
- Optional: small MILP/optimal solver on reduced scenarios, as a ceiling
  comparison

Metrics: response time, % incidents served within SLA, resource
utilization, recovery time post-disruption, fairness across zones.

## Tech stack (proposed)

- **Simulation**: Python, event-driven (SimPy), map as a graph - synthetic
  grid for control, or a real road network via OSMnx for realism/demo
  value.
- **Agents**: hand-rolled negotiation protocol rather than a heavy
  framework (AutoGen/LangGraph) - demonstrates understanding of the MAS
  mechanics rather than gluing an SDK together. LLM backing via API,
  possibly tiered (cheap/fast model for routine bids, stronger model for
  command-level policy reasoning).
- **Dashboard**: live map (React + Leaflet) showing agents, incidents, and
  resource movement in real time - strong for a defense demo.

## Rough scope (one semester)

1. Scenario engine + incident generator + greedy baseline
2. Resource agents + contract-net negotiation (LLM-based bidding)
3. Incident-command policy layer + disruption injection + replanning
4. Evaluation harness across many scenario runs vs. baselines
5. Dashboard + writeup + stress-test larger scenarios

If two-semester: split after step 3 - simulator/protocol first term,
evaluation/polish second.

## Status

Idea stage. No code yet.
