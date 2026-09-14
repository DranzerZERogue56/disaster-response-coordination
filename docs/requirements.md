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

> **EXAMPLE FROM THE COURSE'S OWN SAMPLE — reference only, not yours:**
>
> | Persona | Who they are | What they need | Evidence they exist |
> |---|---|---|---|
> | Dana, 22, the organizer | Buys most of the groceries; keeps a whiteboard list that goes stale | To see, in under ten seconds, what will spoil this week | Interview 2026-02-03; photographed the whiteboard |
> | Marcus, 21, the passive housemate | Will open the app only when something pings him | To be told what to eat tonight without entering anything | Interview 2026-02-04 |
> | The next maintainer | Inherits this repository after the course ends | To understand what each feature was for, from the document alone | Course requirement; Chapter 13 clean-machine test |

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

> **ONE WORKED EXAMPLE FROM THE COURSE'S OWN SAMPLE — reference only, not
> yours. Do not copy, adapt, or reword this into one of your own
> requirements; it's here so you can see all six parts plus rationale,
> source, and acceptance criteria in place at once:**
>
> ### FR-INV-01 — Add a pantry item
>
> **Priority:** Must
> **Requirement:** A signed-in household member shall be able to add an item to the household pantry by supplying a name, a quantity with a unit, and an expiry date.
> **Rationale:** Nothing else in the system works until inventory exists. Dana's whiteboard is the behavior being replaced.
> **Acceptance criteria:**
> - Given a signed-in member on the pantry screen, when they submit a name, quantity, unit, and expiry date, then the item appears in the household pantry list within one page refresh and is visible to every member of that household.
> - Given a submission missing the item name, when the member submits, then the system rejects the submission and states which field is missing.
>
> **Source:** Interview with Dana, 2026-02-03

> **A second worked example showing a `Won't` — note it needs no
> acceptance criteria, since there's nothing to accept:**
>
> ### FR-INV-08 — Export the pantry as a spreadsheet
>
> **Priority:** Won't (this release)
> **Requirement:** A signed-in household member shall be able to export the household pantry as a comma-separated file.
> **Rationale:** Requested once, valued by nobody who was asked a second time. Recorded so the decision is visible rather than forgotten.
>
> **Source:** Interview with Marcus, 2026-02-04

<!-- Repeat this block for every requirement you write. Group by area. -->

### FR-`[ TODO ]`-01 — `[ TODO — short imperative name ]`

**Priority:** `[ TODO — Must | Should | Could | Won't ]`
**Requirement:** `[ TODO — <Actor> shall be able to <action> <object> <under what condition>. ]`
**Rationale:** `[ TODO — why this exists, which persona asked for it ]`
**Acceptance criteria:**
- `[ TODO — Given <starting state>, when <the actor does this>, then <observable thing is true>. ]`
- `[ TODO — Given <edge or failure case>, when <trigger>, then <defined behavior>. ]`

**Source:** `[ TODO ]`

`[ ... repeat for all 18-35 requirements ... ]`

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
