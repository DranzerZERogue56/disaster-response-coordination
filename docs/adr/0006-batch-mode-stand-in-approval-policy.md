# ADR 0006 — Batch-mode proposal decisions use a logged stand-in policy, not a real human

- **Status:** Accepted
- **Date:** 2026-09-30
- **Decider:** Dranzer Rogue
- **Requirements affected:** FR-AGENT-03, NFR-SEC-02; also PROJECT.md's Roster Competition and Evaluation sections, which aren't numbered FR/NFR identifiers but are the other half of this tension
- **Related ADRs:** none upstream; this one resolves a conflict between `PROJECT.md` and `docs/requirements.md` surfaced while drafting Milestone 6's architecture

## Context

`PROJECT.md`'s Roster Competition runs each candidate team size 5-10 times per scenario, unattended, so the "basic descriptive stats (average, how much it varies)" its Evaluation section commits to actually mean something. Nobody sits and watches these runs — that's the whole point of a batch competition.

`docs/requirements.md`'s FR-AGENT-03 (Must) requires escalating any proposal with confidence under 75, or tagged a high severity, to a human dispatcher for approval, modification, or rejection before any resource is dispatched. NFR-SEC-02 makes this a measurable test. Both documents are correct about what they say; they just can't both be literally true at the same time during an unattended run, because there is no human present to do what FR-AGENT-03 requires.

This has to be resolved before the Decide Proposal interface (§5 of `docs/architecture.md`) can be specified, since that interface is exactly the thing both documents are describing.

## Options considered

| Option | Weighted score | The detail that decided it |
|---|---:|---|
| Logged stand-in auto-decide policy in batch mode; real dispatcher reserved for a separate interactive mode | not scored in a matrix — this is a process/policy call, not a technology fit | Lets both documents' real intent survive: batch mode gets its unattended statistical rigor, FR-AGENT-03's human-in-the-loop guarantee still holds in the mode that actually has a human |
| The student personally approves every escalated proposal across all batch runs | not a real option | At a conservative 50 escalations/run × 250 runs (5-10 repeats × 3-5 team sizes × 3-5 scenarios) × even 10 seconds/click, that's roughly 3.5 hours of pure clicking that adds no thinking value to a measurement that's supposed to compare team sizes, not test the student's patience |
| Redefine "roster competition" to mean a handful of human-reviewed runs only | not a real option | `PROJECT.md`'s own Evaluation section already commits to descriptive statistics across repeats; collapsing to one human-reviewed run per team size removes the one piece of evaluation rigor left after the original research-comparison framing was dropped on 2026-09-04 |

## Decision

Batch-mode scoring runs use a documented stand-in policy at the **Decide Proposal** interface: approve if confidence ≥ 60, otherwise log the proposal as `UNRESOLVED_WOULD_ESCALATE` and count it against that run's score rather than blocking the run. The 60 threshold is a design choice made now, not a measured one (see Verification and the revisit trigger below). **Interactive/demo mode is unaffected** — it uses the same interface with a real dispatcher, exactly as FR-AGENT-03 and NFR-SEC-02 specify, with no stand-in involved.

## Consequences

**Positive**

- Unattended batch runs can complete at the 5-10-repeats-per-team-size scale `PROJECT.md` commits to, without silently violating FR-AGENT-03 — the substitution is logged and disclosed, never presented as if a human decided it.

**Negative**

- Roster-competition scores are not a pure measure of "how good is this team size under real human oversight" — some fraction of each run's score reflects the stand-in policy's own accuracy rather than the team's. Mitigation: every `UNRESOLVED_WOULD_ESCALATE` proposal is counted and reported separately in the Report & Visualization Generator's output, so a reader can see how much of a run's performance rode on the stand-in policy versus genuine high-confidence auto-approval. Cost: none additional — this already falls out of the Audit Logger's `decided_by` field, logged either way.
- The 60-confidence threshold is picked without data behind it yet. If it's badly miscalibrated, it could make batch scores a weaker relative comparison between team sizes, even if every team size is affected roughly equally by the same miscalibration.

## Revisit trigger

Revisit this ADR once Milestone 5's Spike SP-03 (LLM confidence-score calibration) actually runs: if the real confidence-score distribution shows the 60-threshold stand-in policy approves fewer than 50% or more than 95% of escalated proposals across a 20-case test batch, the threshold isn't doing real separating work and needs recalibration before any batch score built on it is trusted.

## Verification

Not applicable — this is a process/policy decision, not a vendor fact, so there is no version/price/license claim to source and date.
