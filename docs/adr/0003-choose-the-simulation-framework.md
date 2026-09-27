# ADR 0003 — Choose the simulation/agent framework

- **Status:** Accepted
- **Date:** 2026-09-27
- **Decider:** Dranzer Rogue
- **Requirements affected:** FR-SIM-01, FR-COORD-01, FR-COORD-03, FR-COORD-04, NFR-MNT-01
- **Related ADRs:** 0002 (this framework's agent-stepping model is the other half of the concurrent-write seam that Spike SP-02 measures)

## Context

FR-SIM-01 requires replaying a prewritten sequence of incident reports at a controlled pace, on demand, so the same scenario runs reliably for the capstone defense instead of depending on live data. FR-COORD-01, FR-COORD-03, and FR-COORD-04 require stepping multiple competing agent "teams," resolving conflicting proposals with a defined tiebreak, and applying a consensus timeout across agents — this is the core mechanic the whole capstone is built around, and it needs something to actually advance agents through time steps and collect what each one decided.

The novelty-load count for this project is already high going into this milestone: local Ollama serving and the hand-rolled contract-net negotiation protocol are both new territory. Adding a third and fourth new thing at once (a mapping library and a simulation framework) risks spreading learning time too thin across a 240-hour solo budget. This ADR is where that tradeoff gets made concrete for the simulation layer specifically: Mesa is new to me, but the alternative — writing the scheduler, the agent registry, and the data collection by hand — is arguably *more* novel in aggregate, since it means inventing and debugging that machinery from scratch instead of learning an existing, documented one.

Two real options were evaluated: Mesa (an existing Python agent-based-modeling framework, Apache-2.0) and a hand-rolled loop (a plain Python while-loop with a dict of agents, no framework).

## Options considered

| Option | Weighted score | The detail that decided it |
|---|---:|---|
| Mesa | 3.95 | Built-in scheduler, agent set, and DataCollector cover FR-SIM-01 and FR-COORD stepping directly, with official docs to lean on; costs a real learning curve |
| hand-rolled loop | 3.15 | Faster to a first result since there's no new API, but every piece of scheduling, data collection, and spatial bookkeeping has to be invented and debugged from nothing |

## Decision

We will use **Mesa** as the simulation/agent framework. It is the matrix's top-scored option (3.95 vs. 3.15), and the margin is driven by the criterion this decision cares about most (built-in scheduling/data-collection fit, weighted 0.30) — the one place a hand-rolled loop scored worst (2/5).

## Consequences

**Positive**

- Scheduler, agent registry, and DataCollector are already built and documented, directly covering FR-SIM-01's scripted playback and FR-COORD's need to step multiple competing agents per tick.
- Apache-2.0 licensed, no conflict with the project's MIT license (ADR 0005) or any other dependency in the inventory.
- Reduces total novelty load relative to hand-rolling the same machinery: learning Mesa's existing API is bounded and documented, while inventing an equivalent scheduler from scratch would be open-ended and untested against edge cases Mesa has already handled.

**Negative**

- A new library API to learn on top of Ollama and the hand-rolled contract-net protocol, which are also new this semester — this is the honest cost being accepted, not a "carefully managed" hand-wave. Mitigation: this is the specific tradeoff behind demoting the map/routing decision to a synthetic location graph in ADR 0004, so the total novelty load stays at 3 new things instead of 4 (see the novelty-load section of `docs/tech-evaluation.md`).
- First working Mesa scenario is budgeted at 6-10 hours rather than a same-day result, since the API has to be learned before it can be adapted to a contract-net step.

## Revisit trigger

Revisit this ADR if a first working scripted scenario in Mesa isn't running by the end of Week 7 (the Work Breakdown / Schedule milestone), which is the point at which the assignment's own 2-week cut rule applies: any feature not implemented within 2 weeks of its start gets cut or replaced.

## Verification

| Claim in this ADR | Source | Checked on |
|---|---|---|
| Mesa license: Apache-2.0 | https://github.com/projectmesa/mesa/blob/main/LICENSE | 2026-09-27 |
