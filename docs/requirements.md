# Software Requirements Specification — Disaster Response Coordination

> **Scaffold status:** real course template (`code/srs-template.md`, pulled
> from the course's public code repo), structure unmodified. This
> milestone's AI policy is stricter than Milestone 2's: an assistant may
> ask questions, enumerate missed cases, and attack a sentence for
> ambiguity — **it may not author a requirement.** Every requirement
> sentence below must be typed by you. The worked examples in this file
> (clearly boxed and labeled) are the course's own official sample
> (`code/pantrypilot-requirements-sample.md`), included only to show the
> *shape* of a good requirement — not to be copied, adapted, or reworded
> into your own requirements. Delete the example boxes as you go.

**Author:** `[ TODO ]`  **Version:** 1.0  **Date:** `[ TODO — YYYY-MM-DD ]`
**Status:** Draft
Benjamin Wrenn: V1.1: 9/11/26:


---

## 1. Purpose and Scope

This system is for dispatchers who need a report or proposal on how to respond to an incident. It replaces the slow, manual process of working out a response plan by hand, speeding up that part of the human workflow.

This release is explicitly a proposal/plan system, not a real-time incident response system — it does not handle live incident reports as they happen in the field. It produces a plan a human reviews and acts on, not a live operational tool.

## 2. Stakeholders and Personas

**How many:** 2–3 personas, each naming its evidence, each traced to at least one requirement. One of them must be the next maintainer.

| Persona | Who they are | What they need from the system | Evidence they exist |
|---|---|---|---|
| The veteran dispatcher | A dispatcher with ~10 years experience, handling real-time routing decisions during incidents | Faster, more confident guidance on who to send where — informed by local/building-specific knowledge (blueprints, hazard locations) they can't always have in the moment | Discord conversation, 2026-09-09 — see `docs/elicitation-notes.md` |
| The next maintainer | Whoever inherits this repository after Week 16 — possibly future-you, opening it cold months later | To understand what each requirement was for and why, from the document alone — especially given this project already pivoted once (Week 2, live-demo → roster-competition), so "why" isn't always obvious from the code | Course requirement (Milestone 13's clean-machine test); this repo's own pivot history is concrete proof the need is real, not hypothetical |
| The data-skeptical dispatcher | A second, separate active dispatcher, focused on what makes a response plan trustworthy across many different incident types, not just one scenario | A report that includes supporting situational data alongside the allocation plan — building blueprints, real surrounding geography (not just a basic map), hydrant locations, and per-station responder counts | Reddit comment, r/911dispatchers, 2026-09-13 — see `docs/elicitation-notes.md`. Independently corroborates the veteran dispatcher's point about missing on-scene data. |

## 3. Definitions

| Term | Definition in this document |
|---|---|
| Severity level | The NFPA-style scale: Minor, Moderate, Serious, Severe, Critical (mapping to a 1-5 scale) |
| Confidence score | A 0-100 numeric scale representing the agent's certainty in its own proposal — works like a school grading percentage; higher number, more confident |
| Node | A software process running one agent instance, not necessarily a separate physical machine |
| Lower level agents | A fallback tier of smaller, faster, lower-cost-to-run local models, used when the primary model isn't available or fast enough |

## 4. Assumptions and Dependencies

- **Assumption:** `[ TODO ]` — *If false:* `[ TODO ]`
- **Dependency:** `[ TODO ]` — *If unavailable:* `[ TODO ]`

## 5. Functional Requirements

**How many:** 18–35, grouped by area. Below 18, a 240-hour project is
almost certainly under-specified; above 35, you're specifying at a level
of detail that belongs in the technical specification (Week 6).

**Every requirement needs all six parts, plus rationale and source:**

1. **Identifier** — `FR-<AREA>-<nn>` (e.g. `FR-NEG-01`). Assign once, never reuse; retire by marking Withdrawn, don't renumber.
2. **Actor** — *who* does the thing (usually "the system," or a specific role).
3. **Action** — the verb: *what* happens. One concrete action, not "handles" or "manages."
4. **Object** — *what* the action is done to.
5. **Condition** — the circumstances that trigger or bound it — *this is where vague requirements usually fall apart.*
6. **Priority** — MoSCoW: Must, Should, Could, or Won't (this release).

## FR-INTAKE (incident report intake)

### FR-INTAKE-01 — Field report ingestion

**Priority:** Must
**Requirement:** The system shall accept incident reports coming in from field agents through the intake api, any time a report comes in with the required fields filled in (location, severity, timestamp, reporting unit), doesnt matter if the network is up or down since offline is a requirement too.
**Rationale:** this is the front door of the whole system, if reports cant get in nothing works
**Acceptance criteria:**
- Given a field agent submits a report with all required fields filled in, when the intake api receives it, then the system creates the report and returns a confirmation of successful creation.
- Given the network is down, when a field agent submits a report, then it queues locally; when connectivity returns, then queued reports are sent and processed in timestamp order so a burst of queued reports doesn't overwhelm the system at once.

**Source:** proposal, basic intake needs

### FR-INTAKE-02 — Malformed report rejection

**Priority:** Must
**Requirement:** The system shall reject a report thats missing a required field or has a bad value in it (like a severity outside defined scale), before the report ever reaches an agent for reasoning, and it has to tell the sender what field was wrong so they can fix it and resend.
**Rationale:** garbage in garbage out, if a bad report gets to an agent it could trigger a bad allocation and thats worse in an emergency than just bouncing it back
**Acceptance criteria:**
- Given a report is submitted with one field missing or improperly filled, when the system validates it, then it returns a rejection response identifying that field and, where a regex pattern applies to that field, an explanation of what's wrong with the format.
- Given a report is submitted with multiple bad or missing fields, when the system validates it, then it evaluates fields top-down and returns a rejection response listing all of the bad fields, so the sender sees every problem at once instead of fixing one and resubmitting to find the next.

**Source:** derived from FR-AGENT-01, an agent cant reason on data it cant trust

### FR-INTAKE-03 — Duplicate report detection

**Priority:** Should
**Requirement:** The system shall flag a new report as a possible duplicate of an existing incident, when the new report is within 1 block and 10 minutes of an open incident and the address matches or the event description corroborates the same event, so two field units reporting the same fire dont turn into two separate response chains.
**Rationale:** not critical for a first release but it would look bad in a demo if the same incident spawned two conflicting resource assignments
**Acceptance criteria:**
- Given two reports are submitted within 1 block and 10 minutes of each other, when their addresses match or their event descriptions describe the same kind of event (e.g., "building on fire" and "burning house" both describing a structure fire), then the system tags them as the same incident and combines both reports' data to improve accuracy.
- Given two reports are submitted within 1 block and 10 minutes of each other but their addresses are different, when the system checks them, then it does not merge them and keeps them as separate incidents — the address field is what the system uses to make that distinction.

**Source:** came up thinking through the WebEOC comparison, its a problem they already solved and I dont want to look worse than the incumbent on something this basic

## FR-AGENT (single agent reasoning)

### FR-AGENT-01 — Report severity classification

**Priority:** Must
**Requirement:** The system (agent) shall classify an incoming incident report into a severity level, within 5 seconds of intake, using the fields on the report, not waiting on a human to tag it first.
**Rationale:** severity is what everything else hangs off of, allocation, alerting, escalation, all of it reads this number
**Acceptance criteria:**
- Given a report with all required fields, when the agent classifies it, then classification completes within 5 seconds and the report is tagged with a severity level.
- Given the agent cannot confidently determine a severity level from the report's fields, when classification is attempted, then the report is immediately escalated to a human instead of guessing.

**Source:** proposal, this is basically step one of the agent doing its job

### FR-AGENT-02 — Proposal generation

**Priority:** Must
**Requirement:** The system (agent) shall generate a proposed resource assignment or action for a classified (classified as in given a class/name) incident, after classification finishes, and the proposal has to include which resource its recommending, a confidence score, why, and a list of other possible resources that could be called, not just a yes or no.
**Rationale:** this is the actual reasoning step, if the agent cant produce a proposal with a reason attached then its not really doing agentic reasoning its just doing lookup
**Acceptance criteria:**
- Given a classified incident, when the agent generates a proposal, then the proposal includes the recommended resource, a confidence score, the reasoning why, and a list of other possible resources that could be called.
- Given no available resource is a good fit for the incident, when the agent generates a proposal, then it still produces a proposal (e.g., the best available option) rather than returning nothing.

**Source:** this is the core novelty of the whole project so it has to be in here

### FR-AGENT-03 — Confidence threshold escalation to human

**Priority:** Must
**Requirement:** The system (agent) shall escalate a proposal to a human dispatcher for approval instead of acting on it automatically, whenever the agent's confidence score on that proposal is below 75 (on a 0-100 scale), or the incident is tagged high severity.
**Rationale:** I dont want an agent making an autonomous call on a life safety decision it isnt sure about, this is also probably the thing a defense committee asks about first
**Acceptance criteria:**
- Given a proposal has a confidence score of 75 or above and the incident is not tagged high severity, when the agent finishes reasoning, then the proposal proceeds automatically to the assignment step without requiring human approval.
- Given a proposal has a confidence score below 75, or the incident is tagged high severity, when the agent finishes reasoning, then the proposal is escalated to a human dispatcher, who must approve, modify, or reject it before any resource is actually dispatched.

**Source:** competitive gap analysis, this is what none of the competitors really do (WebEOC and Esri dont reason at all, Palantir doesnt run local)

### FR-AGENT-04 — Agent decision timeout

**Priority:** Should
**Requirement:** The system (agent) shall abandon a reasoning attempt that hasnt produced a proposal, if it runs past ~60 seconds without finishing (rough target, pending actual model selection/benchmarking), at which point it falls back to a non-LLM path and returns an error to the human overseer instead of just hanging.
**Rationale:** local inference on consumer hardware isnt instant, and a hung agent during an actual incident is worse than no agent
**Acceptance criteria:**
- Given a reasoning attempt completes within ~60 seconds, when it finishes, then it produces a proposal as normal.
- Given a reasoning attempt exceeds ~60 seconds without producing a proposal, when the timeout triggers, then the system abandons it, returns an error to the human overseer, and falls back to a non-LLM path instead of continuing to wait.

**Source:** hardware constraint, comes from the local ai server spec (24gb card, not a datacenter)

## FR-COORD (multi agent negotiation)

### FR-COORD-01 — Conflicting resource claim resolution

**Priority:** Must
**Requirement:** The system shall resolve a conflict where two agents propose the same unit for two different incidents, before either assignment is finalized, using a defined tiebreak: severity first, then the amount of useful information in the report, then whichever incident was reported first (always logged, used as the final fallback).
**Rationale:** this is the whole point of calling it multi agent, if conflicts just silently overwrite each other its not coordination its a race condition
**Acceptance criteria:**
- Given two agents propose the same unit for two different incidents, when the tiebreak is applied, then the higher-severity incident wins (or, if tied, whichever has more useful information; if still tied, whichever was reported first), and the resolution is logged as having followed the correct protocol.
- Given the losing agent's incident still needs a unit, when its original proposal is rejected by the tiebreak, then it finds and proposes the next best available unit instead of leaving the incident unassigned.

**Source:** core project goal, decentralized coordination

### FR-COORD-02 — Partial view reconciliation

**Priority:** Must
**Requirement:** The system shall reconcile two agents holding different pictures of the same incident when one has newer info than the other, any time agents share overlapping incident data and the timestamps dont match, favoring the newer report unless a human overrides it.
**Rationale:** decentralized means nobody has the full picture by default, if I dont handle this its not actually decentralized its just one agent pretending to be many
**Acceptance criteria:**
- Given two agents have different timestamped data for the same incident, when reconciliation runs, then the newer data becomes the active record and the older data is kept as history rather than deleted.
- Given a human overrides the automatic reconciliation, when they do, then the override is logged the same way as FR-RES-02's overrides — who did it, when, and what the original automatic decision was.

**Source:** same as above, this is the architecture I pitched

### FR-COORD-03 — Tiebreak rule application

**Priority:** Must
**Requirement:** The system shall apply a consistent tiebreak rule, any time two agent proposals cant both be satisfied with available resources.
**Rationale:** gets its own line separate from COORD-01 because the tiebreak logic gets reused in more places than just the resource claim case
**Acceptance criteria:**
- Given two agent proposals conflict in a way other than claiming the same unit, when the tiebreak applies, then it resolves using the same order as FR-COORD-01: severity, then information richness, then reported-first.
- Given two proposals are truly identical across all tiebreak dimensions, when the tiebreak is applied, then both are validated, but only one is pushed forward/acted on and the other is kept as history rather than discarded.

**Source:** derived from FR-COORD-01

### FR-COORD-04 — Cross agent consensus timeout

**Priority:** Could
**Requirement:** The system shall finalize a decision using the best available proposal instead of waiting indefinitely for every agent to agree, if agents havent reached consensus within 5 minutes, defaulting to whichever proposal has the highest confidence score.
**Rationale:** nice to have so it doesnt stall out live in front of the committee, but the system still works without it if I run out of time
**Acceptance criteria:**
- Given agents reach consensus within 5 minutes, when consensus is reached, then the agreed-upon proposal proceeds normally to the assignment step.
- Given agents haven't reached consensus within 5 minutes, when the timeout fires, then the system finalizes using whichever proposal has the highest confidence score, and the other agents' proposals are kept as history rather than discarded.

**Source:** risk I noticed while thinking through the negotiation logic, agents could in theory just never agree

## FR-RES (resource allocation)

### FR-RES-01 — Unit assignment

**Priority:** Must
**Requirement:** The system shall assign an available resource or unit to an incident, once an agent proposal is approved, either automatically under the FR-AGENT-03 threshold or manually by a dispatcher.
**Rationale:** this is the actual output the whole reasoning pipeline exists to produce
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** proposal

### FR-RES-02 — Manual reassignment override

**Priority:** Must
**Requirement:** A dispatcher shall override any system generated assignment, at any time, and the override has to log who did it and why, it cant just silently replace the agents choice.
**Rationale:** a human always needs the last word here, this is basically a trust requirement not just a functional one
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** same reasoning as FR-AGENT-03, human in the loop

### FR-RES-03 — Resource availability tracking

**Priority:** Must
**Requirement:** The system shall track the current status of every known resource, available, assigned, or out of service, updated in real time as assignments happen, so an agent never proposes a unit thats already committed somewhere else.
**Rationale:** without this the whole allocation piece is just guessing
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** proposal, basic state tracking

## FR-DEGRADE (failure and degraded mode handling)

### FR-DEGRADE-01 — Node failure detection

**Priority:** Must
**Requirement:** The system shall detect when an agent node stops responding, within [X] seconds of the node missing its expected heartbeat.
**Rationale:** for a decentralized system this isnt optional, if a node dies silently the other agents picture of the incident goes stale and nobody knows it
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** architecture requirement, decentralized means it has to handle nodes dying

### FR-DEGRADE-02 — Model load failure fallback

**Priority:** Must
**Requirement:** The system shall fall back to a rules based or manual workflow for that agent, if the local model fails to load or crashes mid session, instead of the agent just going silent.
**Rationale:** ties back to running on a single 24gb card, hardware is going to hiccup sometimes and the demo cant just die because of it
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** local ai server spec, Ollama on consumer gpu

### FR-DEGRADE-03 — Network partition behavior

**Priority:** Should
**Requirement:** The system shall continue operating on locally available data, when a node loses contact with the rest of the network, instead of freezing or refusing to act.
**Rationale:** this is literally the selling point against Palantir, if I dont handle this case the offline and decentralized claim is just marketing
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** competitive gap analysis vs Palantir

### FR-DEGRADE-04 — Degraded mode recovery

**Priority:** Could
**Requirement:** The system shall reconcile state between a reconnected node and the rest of the network, once connectivity is restored after a partition, merging whatever decisions got made independently during the outage.
**Rationale:** this is the hard one honestly, might end up being a stretch goal depending on how the 240 hours goes
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** follows from FR-DEGRADE-03, if you can go offline you eventually have to come back online

## FR-INFER (local inference constraints)

### FR-INFER-01 — Local only model execution

**Priority:** Must
**Requirement:** The system shall run all agent reasoning, entirely on local hardware, zero calls out to an external api or cloud model, even if internet happens to be available.
**Rationale:** this is the other core differentiator besides the multi agent part, if it phones home its just another cloud tool
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** proposal, core architecture decision

### FR-INFER-02 — Response latency bound

**Priority:** Must
**Requirement:** The system shall return an agent response, either a classification or a proposal, within [X] seconds on the target hardware (RTX 3090 or 4090, 24gb vram), not counting network time since its local anyway.
**Rationale:** needs an actual number here I can test against during a demo, "fast" isnt a requirement
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** local ai server spec

### FR-INFER-03 — Hardware capability check

**Priority:** Should
**Requirement:** The system shall verify that the host machine meets minimum requirements (24gb vram, 48gb system ram), on startup, before loading any model, and it should tell the user clearly if it doesnt meet spec instead of just failing weird later.
**Rationale:** saves me a debugging headache later and its an easy one to write
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** local ai server spec

### FR-INFER-04 — Model version pinning

**Priority:** Should
**Requirement:** The system shall record which model and version an agent used to generate a given proposal, every time a proposal is generated, stored alongside the decision in the audit log.
**Rationale:** ties into FR-AUDIT-01, if a model gets swapped later I need to know which version made which call
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** derived from the audit and explainability need

## FR-ALERT (notifications)

### FR-ALERT-01 — Responder notification dispatch

**Priority:** Must
**Requirement:** The system shall notify responders assigned to an incident, within [X] seconds of the assignment being finalized.
**Rationale:** an assignment nobody gets told about didnt actually happen
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** proposal, basic notification need

### FR-ALERT-02 — Notification acknowledgment tracking

**Priority:** Should
**Requirement:** The system shall record whether a notified responder has acknowledged the alert, for every alert sent, and if no ack comes back within [X] minutes it should flag that to the dispatcher.
**Rationale:** an alert that went out and got ignored is functionally the same as no alert, and dispatch should know that
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** gap I noticed comparing to how alerting usually works in these systems

## FR-MAP (geospatial display)

### FR-MAP-01 — Zone boundary display

**Priority:** Should
**Requirement:** The system shall display the boundary of an active incident zone, on the operator dashboard, updated whenever the zone gets redefined.
**Rationale:** more of a UI nicety than core to the reasoning claim, so it can slip first if time gets tight
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** proposal, situational awareness

### FR-MAP-02 — Unit position tracking

**Priority:** Could
**Requirement:** The system shall display the current location of assigned units, on the same dashboard, if location data is even available from the unit (might not be in scope depending on what data I actually have access to).
**Rationale:** not sure this is realistic for a solo 240 hour build unless I fake the location feed, flagging it low priority on purpose
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** nice to have, not core to the pitch

## FR-AUDIT (decision logging and explainability)

### FR-AUDIT-01 — Decision trail logging

**Priority:** Must
**Requirement:** The system shall log every proposal an agent generates, including what data it used and its confidence score, at the moment the proposal is generated, before its approved or rejected, so the log reflects the agents actual reasoning and not just the final outcome.
**Rationale:** probably the single most important requirement for the defense, if I cant show why an agent did something the whole "trustworthy AI in emergencies" argument falls apart
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** came out of thinking about what a reviewer would push back on, explainability

### FR-AUDIT-02 — Human override logging

**Priority:** Must
**Requirement:** The system shall log any time a dispatcher overrides an agent decision, capturing who did it, when, and what the original agent proposal was so its comparable later.
**Rationale:** same reasoning as above, and it also gives me real data afterward to see how often the agents were actually right
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** derived from FR-RES-02

## FR-AUTH (access control)

### FR-AUTH-01 — Role based access control

**Priority:** Must
**Requirement:** The system shall restrict which actions a user can take, like a dispatcher being able to override versus an observer only being able to view, based on the role assigned to their account at login.
**Rationale:** not exciting but its a baseline expectation for anything touching emergency response, and its cheap to build early
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** standard requirement, not project specific

## FR-SIM (demo and testing support)

### FR-SIM-01 — Scripted incident playback

**Priority:** Must
**Requirement:** The system shall replay a prewritten sequence of incident reports at a controlled pace, on demand, so I can run the same scenario reliably for the capstone defense demo instead of hoping live data behaves.
**Rationale:** not walking into my defense relying on live data working right the first time, this is basically insurance for demo day
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** personal experience, dont trust live demos

## 6. Non-Functional Requirements

Placeholder for Week 4. Leave this empty — do not write vague quality
words here now ("the system shall be secure"); fill it in when each one
can be made measurable.

## 7. Out of Scope (the Won't-Have List)

**How many:** at least 5 rows, each with a reason and a revisit condition.

> **EXAMPLE FROM THE COURSE'S OWN SAMPLE — reference only, not yours:**
>
> | Not building | Why not | Revisit when |
> |---|---|---|
> | Shopping list generation | A second feature area with its own data model; costs an estimated 25 hours the budget does not have | After a v1.0 release exists |
> | Multiple households per account | No evidence any interviewed user wants it | A second household asks |
> | Native mobile applications | Doubles the build and the release process | Out of scope permanently |

| Not building | Why not | Revisit when |
|---|---|---|
| `[ TODO ]` | | |

## 8. Open Questions

| # | Question | Who can answer it | Needed by |
|---|---|---|---|
| `[ TODO ]` | | | |

## 9. Document Change Log

| Date | Version | Change | Reason |
|---|---|---|---|
| `[ TODO — YYYY-MM-DD ]` | 1.0 | Initial specification | Milestone 3 |

---

## Reminder: mirroring Musts onto the project board

Every Must-priority requirement identifier needs its own card on the
project board built for Milestone 2
(https://github.com/users/DranzerZERogue56/projects/1) — title the card
with the identifier itself, e.g. a card titled `FR-NEG-01`, not a
paraphrase of it. That way a grader (or you, in Week 12) can match board
state to spec state at a glance. Do this after the requirements below
are real, not before — a card for a requirement that doesn't exist yet
is just noise.
