# Disaster Response Coordination

Senior capstone project. Solo, one semester, 240 hours total (see
`CALENDAR.md` for the week-by-week schedule and graded deliverables).
Focus areas: agentic AI, multi-agent systems, software architecture. No
audio component and no real-world/adversarial "manipulation" framing —
this is a defensive/logistics coordination system, entirely
simulation-based.

## Problem

Simulate a large-scale disaster (earthquake, flood, mass-casualty event)
unfolding over a map. Incidents appear over time with location, severity,
type, and resource needs. Scarce resources (ambulances, fire units, shelter
capacity, medical supplies) must be allocated and continuously re-allocated
as the situation changes: new incidents spike, roads close, a hospital hits
capacity, a unit breaks down.

## Objective

Give the system a disaster scenario in plain English — an earthquake
hitting a city, a flood, a mass-casualty event. It works out which kinds
of responders would be needed (medics, firefighters, shelter/logistics
crews, security), then tries a handful of different team sizes against a
simulated version of that disaster. Every team uses the same approach to
decide who goes where — responders "talk" to each other in plain language
and negotiate assignments, the way a real dispatcher radios instructions
during an emergency, rather than following a fixed formula. Whichever
team size handles the scenario best gets written up as a suggested
response plan: a document a company or agency could keep on file and
reuse the next time something like this happens.

This is not a research comparison between negotiation styles anymore —
an earlier version of this project set out to test whether letting
responders reason in plain language beats classic optimization math.
That question is dropped. The one thing still checked, as a sanity check
rather than a thesis, is whether the winning team's plan is actually
better than the dumbest possible approach (just sending the nearest
available unit to each incident, no negotiation at all) — if it isn't,
that's a sign something is broken, not a finding worth reporting.

## Architecture

- **Resource agents** — one program "role" per kind of responder:
  **Medical, Fire, Shelter/Logistics, Security**. Each keeps track of its
  own units — how many it has, where they are, what they're already
  committed to, how long until they arrive. How many units each role
  gets in a given run — the team size — is exactly what's being tried
  out and compared (see Roster competition below); everything else about
  how a role behaves is identical no matter which team size is being
  tested.
- **Incident-command role** — doesn't decide who goes where. It sets the
  ground rules the responders negotiate under (e.g. "protect people over
  property," "sickest patients first," "keep zone B covered, storm's
  coming"). This role reasons in plain language rather than following a
  fixed checklist, so it can adjust its guidance as the situation
  changes. Its reasoning is also where the final written report's
  explanation comes from — the plan's rationale is built from the same
  reasoning the command role actually used during the run, not written
  up separately after the fact.
- **Scenario reader** (new) — reads the plain-English scenario
  description (whether it's one written ahead of time or typed in on the
  spot) and turns it into the specifics the simulation needs: which
  responder roles are relevant, roughly how big the disaster is, which
  city's streets to use, what disruptions to throw at it partway
  through, and which team sizes to try. Both the pre-written scenarios
  and anything typed in live go through this same step, so the rest of
  the system never has to treat them differently.
- No single role has full authority over every truck and ambulance in
  the simulation — responders negotiate directly with each other
  instead, closer to how real agencies actually coordinate, and there's
  no single point of failure if one role gets stuck.

## Scenario input

Two ways a scenario gets in, both ending up in the same place (fed
through the scenario reader above):

1. **A handful of scenarios written ahead of time** (3–5, covering things
   like an earthquake, a flood, a mass-casualty event) — these are the
   ones used for the semester's graded evaluation runs, so results stay
   repeatable.
2. **Typed in on the spot, in plain English** — used to show off that
   the system isn't hardcoded to only handle the pre-written scenarios
   (e.g. at the final presentation). Not used for the graded evaluation
   runs, since it hasn't been checked ahead of time the way the
   pre-written set has.

## Negotiation protocol

Responders use a simple announce → bid → award pattern to hand off work
— one responder announces "I need help covering incident X," others bid
on whether/how they can help, and the announcer picks a bid. This
pattern (called a **contract-net protocol** in the multi-agent-systems
literature) is hand-built from scratch here rather than pulled from a
heavy off-the-shelf agent framework (like AutoGen or LangGraph) —
building it directly demonstrates actually understanding how the
negotiation works, which matters for a capstone graded on architecture
decisions, not just working software.

The key mechanism: bids aren't computed from a fixed formula. Each
responder reasons about its bid in plain language via the LLM, so it can
flag tradeoffs a formula would miss — e.g. "I can cover this, but zone B
goes uncovered for 10 minutes given the storm forecast — is that
acceptable?"

## Roster competition

For a given scenario, a handful of candidate team sizes get tried — e.g.
a medical-heavy team, a balanced team, a security-heavy team. Every
candidate runs through the exact same simulation and negotiation process
against the exact same scenario (same incidents, same streets, same
disruptions) — the only thing that changes is how many of each responder
type is on the team. Each run gets scored (see Evaluation) and ranked,
and the highest-scoring team size becomes the plan that gets written up
and recommended for that scenario.

How many team sizes get tried per scenario is still an open decision —
**TODO**, starting point is 3–5, to be revisited once real run times are
known from the week 9 walking skeleton.

## Replanning under disruption

The main evaluated capability, not just initial allocation. Mid-scenario,
inject all three disruption types:

- **Road closure**
- **Unit failure/breakdown**
- **Incident surge**

Agents must renegotiate committed assignments quickly. Recovery speed and
quality after a disruption is where cascading failures happen in real
incidents, and where the system is actually tested.

## Report generation

After a scenario's team-size competition finishes, the system writes up
a report — the actual document a company or agency could plausibly use
as their on-file response plan. Each report includes:

- **A plain-language explanation of why this team and this plan** —
  pulled from the incident-command role's own reasoning during the
  winning run, not written up separately after the fact.
- **A table/timeline** of exactly which units went where and when,
  including how disruptions were handled.
- **A comparison** against the other team sizes that were tried and the
  naive baseline, showing the scores that decided the winner.
- **Fairness notes** — did any one neighborhood/zone get worse service
  than the rest?
- **What was assumed or guessed** when turning the scenario description
  into simulation details, plus general caveats (this is a small
  exploratory simulation, not a guarantee).

**Format (proposal, not locked):** one Markdown file per scenario run
(e.g. `reports/<scenario-slug>-<timestamp>.md`), filled in from a
template using the run's own logged data — not hand-written each time.
Markdown keeps it free, easy to diff, and viewable straight on GitHub.
Turning it into a nicer PDF/HTML version is a nice-to-have, not a
requirement.

## Tech stack (locked)

Everything below is free, open-source, and usable without creating any
account or API key — a hard constraint for this project (the only money
in scope is the optional local hardware in `HARDWARE.md`).

- **Simulation engine**: **Mesa 3.x** (a Python library for building
  simulations with many independent agents). Chosen over writing a tick
  loop by hand or using bare SimPy because of its `AgentSet` API (makes
  it easy to filter/group/activate different kinds of agents) and its
  scheduling tools — a good fit for "lots of independent agents sharing
  one map." Note: Mesa 3 moved its own visualization tools into a
  separate, still-experimental system (`SolaraViz`) and doesn't install
  all of it by default — doesn't matter here, since this project has no
  live/interactive visualization at all (see Visualization below).
- **Map**: a real road network via **OSMnx** (pulls an actual city's
  street layout straight from OpenStreetMap — no API key, no account
  needed). A quick throwaway test in **weeks 5–6** checks whether the
  city graph actually loads and can be routed on, and decides go/no-go
  before committing further. If that test fails, the fallback is a
  made-up grid of streets instead of a real city (see `RISKS.md`).
- **LLM backend**: **Ollama** (runs a language model locally on your own
  machine, free, no account). Every call to a language model in this
  project goes through one shared interface from week 2 onward, so
  swapping which model or backend is used later stays a small change —
  but **paid APIs (Anthropic, OpenAI, etc.) are explicitly off the table
  for this project**: they cost money and need accounts, which this
  project isn't allowed to use. If the local model isn't good enough,
  the fix is a smaller scenario or a better local model, never a paid
  API.
- **Negotiation**: the hand-built bidding process described above (not a
  framework like LangGraph or AutoGen).
- **Visualization (final-demo output)**: no live map. Instead, a static
  picture or short recorded animation of the winning team's run for one
  scenario — built with Matplotlib and OSMnx's own map-drawing tools,
  generated after a run finishes from what was logged during it. Not
  live, not interactive, doesn't need a network connection at
  presentation time — this removes the two risks the earlier live-map
  plan carried (a crash mid-demo, or losing the venue's network).
- **Baseline** (see Evaluation): plain Python, one simple "just send the
  nearest available unit" assignment — the only baseline kept. Two other
  comparison methods that were originally planned (a version with no
  language-model reasoning at all, and a formal math-based optimal
  solver) are both dropped — this project no longer needs to argue one
  coordination method beats another, so there's nothing left to compare
  in the stack. No PuLP/MILP-solver dependency.
- **Report generator**: plain Python plus simple templating (e.g.
  Jinja2, or just Python f-strings if the template stays simple) — fills
  in a Markdown report from a run's logged data. No new account or
  network dependency.
- **Scenario reader**: uses the same Ollama-based interface as the
  responders and the incident-command role — no new dependency, just a
  new kind of request/response (plain-English scenario text in,
  structured simulation settings out).

## Scope & scale

- **Scenario scale**: medium — roughly 30–50 incidents and 25–40
  responder units per scenario. Big enough to feel like a real disaster
  and put real pressure on the negotiation, small enough to stay
  debuggable while running on a local language model.
- **Resource categories**: all four (Medical, Fire, Shelter/Logistics,
  Security).
- **Disruption types**: all three (road closure, unit failure, incident
  surge).
- **Team sizes tried per scenario**: **TODO** — starting point 3–5 (see
  Roster competition).
- **Scenarios**: 3–5 written ahead of time for the graded evaluation,
  plus the ability to type one in live for the demo (see Scenario
  input).

## Evaluation

**Baseline**: just send the nearest available unit to each incident, no
negotiation at all — the one comparison method kept, as a floor to check
against. The other two comparison methods originally planned (a version
with no language-model reasoning, and a formal optimal-solver ceiling)
are both dropped.

**Effectiveness score**: the same five measurements as before, combined
into one overall score used to rank the competing team sizes and pick a
winner:
- How fast responders reach incidents
- What % of incidents get served within the target time
- How much of each responder team actually gets used
- How fast the team recovers after a disruption
- Fairness across zones — does any one neighborhood systematically get
  worse service than the rest?

**Weights: TODO** — how much each of those five counts toward the
overall score is still an open decision. Starting point is to weight
them all equally; real weights (with reasoning behind them) should be
picked before this ranking is used for anything graded.

**Rigor**: each team size gets run 5–10 times per scenario, with basic
descriptive stats (average, how much it varies) — same rigor as
originally planned, just organized around team sizes instead of
coordination methods. Still an exploratory look, not a claim backed by a
large number of trials.

**Output**: whichever team size scores highest, its score, the other
team sizes' scores, and the naive baseline's score all feed into the
written report and the after-the-fact visualization.

## Reproducibility

A scripted setup (install what's needed, pull a small Ollama model) so a
grader can plausibly run this on a clean machine, per the Milestone 13
documentation requirement — no account signup or API key needed anywhere
in that path, including reproducing a full team-size competition and its
written report. Anything that depends on a language model is
mockable/stubbed in tests, including the scenario reader, so automated
testing doesn't need a live model running.

## Testing

Full test pyramid, sized for a solo 240-hour budget:
- Unit tests on core logic (bid scoring, contract awards, disruption
  handling)
- Scenario-replay regression tests (fixed scenarios with known expected
  outcomes)
- Property-based/fuzz tests on generated scenarios (e.g. a resource
  should never be double-booked)
- A structural check on the scenario reader's output (does the parsed
  scenario have the shape the rest of the system expects? — a sanity
  check on structure, not a grade on how creative the interpretation is)

## CI

GitHub Actions runs the full test suite, including scenario-replay
tests. Anything that calls a language model — bidding, the
incident-command role's reasoning, or the scenario reader — must be
mockable so CI doesn't need a live model running or cost anything on
every push.

## Final presentation

No live/interactive demo. One scenario gets fed in during the
presentation — either one of the pre-written ones, or typed live to show
off the scenario reader — and the team-size competition can just
run/print its progress in a terminal window, no live rendering needed,
so a slow response from the language model mid-presentation isn't a real
risk anymore. The presentation then walks through: (1) the written
report for that scenario, and (2) the pre-made picture or short
animation of the winning team's run. A fully pre-recorded terminal run
is kept as a rehearsed backup in case the live run misbehaves — but the
stakes are much lower than the original live-map plan, since neither the
report nor the visualization actually depends on anything happening
live.

## Scope discipline

This project still stacks several non-trivial pieces into a solo
240-hour budget: Mesa, a real road network via OSMnx, language-model-
based negotiation, reading scenarios written in plain English, trying
multiple team sizes per scenario, one naive baseline, writing up a
report, and a full test suite with CI — see `RISKS.md` for the specific
risk this creates. If behind schedule, cut in this order:

1. Try fewer team sizes per scenario (just a number to change, no
   redesign needed)
2. Drop property-based/fuzz tests (keep unit + scenario-replay tests)
3. Simplify the final-demo visualization down to one still image, drop
   the short animation
4. Write fewer scenarios ahead of time (5 down to 3)
5. Fall back from a real city's streets to a made-up grid — decided by
   the weeks 5–6 test, not left until week 13
6. Shrink scenario scale from medium down to small (~10–20 incidents)
7. Drop typing a scenario in live as a demo feature, fall back to only
   the pre-written scenarios for the presentation (the scenario reader
   itself still gets used either way, since the pre-written scenarios go
   through it too — so this isn't wasted work)

## Rough scope (one semester, aligned to CALENDAR.md)

1. Scenario engine (Mesa) + incident generator + naive baseline
2. Resource agents + bidding/negotiation (language-model-based, via
   Ollama, behind a swappable interface)
3. Incident-command reasoning role + disruption injection + renegotiation
4. Scenario reader (turns plain-English scenario text into simulation
   settings, including which team sizes to try)
5. Team-size competition harness (run several candidate team sizes per
   scenario through the same pipeline)
6. Evaluation harness (weighted scoring, comparison against the naive
   baseline, fairness measurement) across team-size runs
7. Report generator (Markdown template + the incident-command role's own
   reasoning)
8. Full test pyramid + CI (including a structural check on the scenario
   reader's output)
9. Real road network integration (OSMnx) + after-the-fact visualization
   for the final demo
10. Writeup, documentation set, clean-machine reproducibility script
11. Finalize the pre-written scenario set, stress-test larger scenarios,
    presentation deck, demo rehearsal

## Status

Concept scaled and locked to fit the 16-week/240-hour solo calendar.
Pivoted in Week 2 (2026-09-04) from an earlier version that set out to
prove one negotiation style beats classical optimization, with a live
real-time map as the demo centerpiece — this version instead focuses on
trying different team sizes against a scenario and producing a usable
written plan, no live map. No code yet.
