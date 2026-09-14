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

`[ TODO — one paragraph: what this system is for, who it serves, what problem it removes. One paragraph: what's explicitly outside the boundary of this release. If your requirement count falls outside 18-35, defend it here in two sentences. ]`

> Requirement areas are being worked out in `docs/to-review.md` (staging
> file, not part of the submission) before landing here as full
> six-part requirements.

## 2. Stakeholders and Personas

**How many:** 2–3 personas, each naming its evidence, each traced to at least one requirement. One of them must be the next maintainer.

| Persona | Who they are | What they need from the system | Evidence they exist |
|---|---|---|---|
| The veteran dispatcher | A dispatcher with ~10 years experience, handling real-time routing decisions during incidents | Faster, more confident guidance on who to send where — informed by local/building-specific knowledge (blueprints, hazard locations) they can't always have in the moment | Discord conversation, 2026-09-09 — see `docs/elicitation-notes.md` |
| The next maintainer | Whoever inherits this repository after Week 16 — possibly future-you, opening it cold months later | To understand what each requirement was for and why, from the document alone — especially given this project already pivoted once (Week 2, live-demo → roster-competition), so "why" isn't always obvious from the code | Course requirement (Milestone 13's clean-machine test); this repo's own pivot history is concrete proof the need is real, not hypothetical |
| The data-skeptical dispatcher | A second, separate active dispatcher, focused on what makes a response plan trustworthy across many different incident types, not just one scenario | A report that includes supporting situational data alongside the allocation plan — building blueprints, real surrounding geography (not just a basic map), hydrant locations, and per-station responder counts | Reddit comment, r/911dispatchers, 2026-09-13 — see `docs/elicitation-notes.md`. Independently corroborates the veteran dispatcher's point about missing on-scene data. |

## 3. Definitions

`[ TODO — every term your requirements use in a project-specific sense. If a reader could interpret a word two ways, it belongs here. ]`

| Term | Definition in this document |
|---|---|

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
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** proposal, basic intake needs

### FR-INTAKE-02 — Malformed report rejection

**Priority:** Must
**Requirement:** The system shall reject a report thats missing a required field or has a bad value in it (like a severity outside defined scale), before the report ever reaches an agent for reasoning, and it has to tell the sender what field was wrong so they can fix it and resend.
**Rationale:** garbage in garbage out, if a bad report gets to an agent it could trigger a bad allocation and thats worse in an emergency than just bouncing it back
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** derived from FR-AGENT-01, an agent cant reason on data it cant trust

### FR-INTAKE-03 — Duplicate report detection

**Priority:** Should
**Requirement:** The system shall flag a new report as a possible duplicate of an existing incident, when the location and time are close enough to an open incident (need to define the actual radius/window still, TBD), so two field units reporting the same fire dont turn into two separate response chains.
**Rationale:** not critical for a first release but it would look bad in a demo if the same incident spawned two conflicting resource assignments
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** came up thinking through the WebEOC comparison, its a problem they already solved and I dont want to look worse than the incumbent on something this basic

## FR-AGENT (single agent reasoning)

### FR-AGENT-01 — Report severity classification

**Priority:** Must
**Requirement:** The system (agent) shall classify an incoming incident report into a severity level, within [x] seconds of intake, using the fields on the report, not waiting on a human to tag it first.
**Rationale:** severity is what everything else hangs off of, allocation, alerting, escalation, all of it reads this number
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** proposal, this is basically step one of the agent doing its job

### FR-AGENT-02 — Proposal generation

**Priority:** Must
**Requirement:** The system (agent) shall generate a proposed resource assignment or action for a classified (classified as in given a class/name) incident, after classification finishes, and the proposal has to include which resource its recommending and why, not just a yes or no.
**Rationale:** this is the actual reasoning step, if the agent cant produce a proposal with a reason attached then its not really doing agentic reasoning its just doing lookup
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** this is the core novelty of the whole project so it has to be in here

### FR-AGENT-03 — Confidence threshold escalation to human

**Priority:** Must
**Requirement:** The system (agent) shall escalate a proposal to a human dispatcher for approval instead of acting on it automatically, whenever the agents confidence score on that proposal falls below a set threshold (still need to pick the actual number), or the incident is tagged high severity.
**Rationale:** I dont want an agent making an autonomous call on a life safety decision it isnt sure about, this is also probably the thing a defense committee asks about first
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** competitive gap analysis, this is what none of the competitors really do (WebEOC and Esri dont reason at all, Palantir doesnt run local)

### FR-AGENT-04 — Agent decision timeout

**Priority:** Should
**Requirement:** The system (agent) shall abandon a reasoning attempt that hasnt produced a proposal, if it runs past [X] seconds without finishing, at which point it falls back to a default or manual path instead of just hanging.
**Rationale:** local inference on consumer hardware isnt instant, and a hung agent during an actual incident is worse than no agent
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** hardware constraint, comes from the local ai server spec (24gb card, not a datacenter)

## FR-COORD (multi agent negotiation)

### FR-COORD-01 — Conflicting resource claim resolution

**Priority:** Must
**Requirement:** The system shall resolve a conflict where two agents propose the same unit for two different incidents, before either assignment is finalized, using a defined tiebreak (severity first, then whichever incident was reported first, still need to lock this rule down).
**Rationale:** this is the whole point of calling it multi agent, if conflicts just silently overwrite each other its not coordination its a race condition
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** core project goal, decentralized coordination

### FR-COORD-02 — Partial view reconciliation

**Priority:** Must
**Requirement:** The system shall reconcile two agents holding different pictures of the same incident when one has newer info than the other, any time agents share overlapping incident data and the timestamps dont match, favoring the newer report unless a human overrides it.
**Rationale:** decentralized means nobody has the full picture by default, if I dont handle this its not actually decentralized its just one agent pretending to be many
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** same as above, this is the architecture I pitched

### FR-COORD-03 — Tiebreak rule application

**Priority:** Must
**Requirement:** The system shall apply a consistent tiebreak rule, any time two agent proposals cant both be satisfied with available resources.
**Rationale:** gets its own line separate from COORD-01 because the tiebreak logic gets reused in more places than just the resource claim case
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

**Source:** derived from FR-COORD-01

### FR-COORD-04 — Cross agent consensus timeout

**Priority:** Could
**Requirement:** The system shall finalize a decision using the best available proposal instead of waiting indefinitely for every agent to agree, if agents havent reached consensus within [X] seconds, defaulting to whichever proposal has the highest confidence score.
**Rationale:** nice to have so it doesnt stall out live in front of the committee, but the system still works without it if I run out of time
**Acceptance criteria:**
- `[ TODO — Given..., when..., then... ]`
- `[ TODO — Given <failure case>..., when..., then... ]`

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
