# ADR 0007 — Information richness is a documented score: distinct content words, plus two fixed bonuses

- **Status:** Accepted
- **Date:** 2026-11-05
- **Decider:** Dranzer Rogue
- **Requirements affected:** FR-COORD-01 and FR-COORD-03 (the tiebreak: severity first, then information richness, then reported-first)
- **Related ADRs:** ADR 0006 (another policy decision that has to be written down so it can be checked)

## Context

FR-COORD-01 says that when two proposals conflict, the higher-severity incident wins, "or, if tied, whichever has more useful information". It does not say what "more useful information" is, how it is counted, or how its parts are weighed against each other. A tiebreak that nobody can recompute is a coin toss with extra steps, and it has to give the same winner on every run (the Resolve Negotiation Conflict contract says resolving the same pair twice returns the same winner). Ben asked (decision D5) for the definition, the quantification and the weights to be explicit.

## Decision

The richness of a report is a whole number computed from three fields the sender supplied: `severity_raw`, `description` and `location`. Higher is richer. It is the sum of three parts:

| Part | How it is counted | Weight | Why |
|---|---|---|---|
| **Distinct content words** | Lower-case the text of `severity_raw` and `description` together, split it into words of two or more letters, drop a fixed list of common stop words (a, an, the, and, or, of, to, in, on, at, is, are, was, were, not, no, it, this, that, with, for, from, by, be, has, have, had, there, their, then, so, but), and count how many *different* words remain | **1 point each** | Each new word is a new fact; saying the same word again is not. Counting distinct words means padding a report with repeats earns nothing |
| **A separate description was supplied** | The optional `description` field is present and not blank | **+2** | A sender who took the trouble to add detail beyond the required fields has given information the other sender did not, even before counting the words in it |
| **A specific location** | `location` contains a standalone number (a street or building number such as `900` or `12`; an ordinal like `2nd` does not count) or an intersection marker (`&`, the word `and`, or `/`) | **+2** | A responder can drive to "4th & Main St" and cannot to "near the old warehouse"; location precision is the most actionable single piece of information |

`richness = distinct_content_words + (2 if description supplied) + (2 if location is specific)`. It is deterministic: the same report always scores the same.

**Where it is used.** Only as the second step of the tiebreak, after severity and before reported-first. A report with higher severity wins however rich the other one is.

**What it is not.** It is not a measure of truthfulness or quality; a long wrong report scores high. It is a stand-in for "how much has the sender told us" that can be recomputed by a stranger from the three fields.

## Consequences

- The tiebreak is explainable: the log can store the two scores and the reader can recompute them.
- The weights are choices, not facts. If a real dispatcher says location precision matters more (or less), the weights change in one place (`src/negotiation/tiebreak.py`) and the tests that pin them change with them.
- Gaming is possible (a sender can list many distinct words) and is accepted for this release because every report is synthetic and the tiebreak only matters after severity.
- Property tests pin the shape: adding a new distinct word raises the score by exactly 1, repeating words changes nothing, and the score never goes below 0.
