# ADR 0005 — Choose the project license

- **Status:** Accepted
- **Date:** 2026-09-27
- **Decider:** Dranzer Rogue — you are the architect this semester
- **Requirements affected:** none directly (a project-level decision, not tied to a single FR/NFR); constrains every dependency choice in ADRs 0001-0004
- **Related ADRs:** 0001, 0002, 0003, 0004 (each depends on this one having landed, since it sets the compatibility bar for every dependency license in the inventory below)

## Context

This was flagged as a deferral back in Week 1: "MIT leading, GPL-3.0-only as backup," with the reason being that the license didn't matter much at that stage and the priority was letting other people take the project and use it. Milestone 5 is where that deferral has to resolve, since a real `LICENSE` file and its justification are graded rubric lines this week.

The two candidates are MIT (permissive: anyone can use, modify, and redistribute, including in closed-source or commercial work, with only the copyright notice preserved) and GPL-3.0-only (copyleft: anyone can use and modify, but any distributed derivative work must also be released under GPL-3.0). The project's own stated goal — "I want other people to take it" — points toward the license with the fewest conditions attached to reuse. A capstone demo aimed at showing dispatchers and agencies a proof of concept benefits from the lowest possible barrier for someone to fork it, adapt it to their own department's stack, or fold pieces of it into a commercial tool without having to open-source their own additions.

The dependency licenses gathered for this milestone (Ollama: MIT, Mesa: Apache-2.0, OSMnx: MIT, SQLite: public domain) are all permissive and compatible with either MIT or GPL-3.0 on the project's own side, so compatibility does not force the choice — it comes down to what obligation the project wants to place on downstream users.

## Options considered

| Option | Weighted score | The detail that decided it |
|---|---:|---|
| MIT | not scored in the matrix — this is a policy call, not a technical fit | Fewest conditions on reuse; matches the stated "I want other people to take it" goal; compatible with every dependency license already in the inventory |
| GPL-3.0-only | not scored in the matrix | Would force any derivative distributed to the public to also be GPL-3.0, which cuts against a dispatcher agency or a company wanting to adapt this privately without releasing their changes |

This decision wasn't run through the weighted matrix in `tech-evaluation.csv` because it isn't a technical fit question with measurable criteria — it's a values call about how much obligation to place on someone downstream. That call belongs to a written decision, not a score.

## Decision

We will license the project under the **MIT License** (SPDX: `MIT`), copyright held by Dranzer Rogue, effective 2026-09-27. The `LICENSE` file at the repository root carries the full text.

## Consequences

**Positive**

- Anyone — a dispatch agency, a classmate, a company — can fork, modify, and redistribute the project, including inside closed-source work, with no obligation beyond keeping the copyright notice. This directly serves the stated goal of wanting other people to take it.
- No license-compatibility friction with any dependency in the current inventory (Ollama, Mesa, OSMnx, SQLite are all permissive or public domain).

**Negative**

- Anyone can also take the project, build a closed commercial product on top of it, and never contribute anything back or credit the work beyond the copyright line. There is no reciprocity requirement.
- If this project were ever spun into a company or product the author wanted to keep control over, MIT gives no leverage to prevent a competitor from taking the exact codebase. Mitigation: none budgeted this semester — the explicit tradeoff being accepted here is openness over control, and reversing it later (relicensing) is legally only possible for code the author still solely owns, which is true today but would need re-checking before any future relicense.

## Revisit trigger

Revisit this ADR if the project is ever taken toward commercial or agency deployment beyond the capstone (i.e., past Week 16 with an actual dispatcher agency expressing interest in adoption) **or** if a dependency is added whose license (e.g., AGPL-3.0) is incompatible with MIT redistribution — check the license inventory in `docs/tech-evaluation.md` before adding any new dependency to catch this before it happens.

## Verification

| Claim in this ADR | Source | Checked on |
|---|---|---|
| Ollama license: MIT | https://github.com/ollama/ollama/blob/main/LICENSE | 2026-09-27 |
| Mesa license: Apache-2.0 | https://github.com/projectmesa/mesa/blob/main/LICENSE | 2026-09-27 |
| OSMnx license: MIT | https://github.com/gboeing/osmnx/blob/main/LICENSE.txt | 2026-09-27 |
| SQLite: public domain | https://sqlite.org/copyright.html | 2026-09-27 |
| MIT license permits closed-source redistribution with only notice preservation; GPL-3.0-only requires derivative works distributed to the public to also be GPL-3.0 | https://opensource.org/license/mit and https://www.gnu.org/licenses/gpl-3.0.en.html | 2026-09-27 |
