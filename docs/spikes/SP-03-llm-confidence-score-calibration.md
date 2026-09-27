# Spike SP-03 — Is llama3.2:3b's self-reported confidence score meaningful enough to gate human approval?

- **Unknown:** Whether a 0-100 confidence score produced by `llama3.2:3b` actually separates proposals that should auto-dispatch from ones that need a human, or whether it's just noise that happens to look like a number.
- **Feeds:** ADR 0001 — local language model (its revisit trigger names this exact question)
- **Requirements at risk:** NFR-SEC-02, FR-AGENT-03
- **Time box:** 3 hours
- **Run on:** not yet run — planned for after real negotiation runs exist (ASM-03's own verify-by date is end of Week 10)

## The question

Across a batch of seeded proposals with known "should this auto-dispatch" answers, does the model's confidence score correctly place proposals below 75 into the "needs human review" bucket and proposals at or above 75 into "safe to auto-dispatch," at least 8 times out of 10?

## The smallest thing that answers it

A script that feeds 10 seeded incident reports with a pre-labeled correct severity/confidence outcome (a mix of clear-cut and ambiguous cases) through the classification step, records the model's confidence score for each, and compares the score's above/below-75 bucket against the pre-labeled correct bucket.

## Success criterion

8 or more of 10 seeded cases land in the correct bucket (auto-dispatch vs. human-review) relative to the pre-labeled expected outcome.

## Failure criterion

Fewer than 8 of 10 land correctly, or the confidence score clusters so tightly (e.g., everything scores 70-80) that the 75 threshold isn't actually doing any separating work.

## Plan B if it fails

Recalibrate the threshold using the observed score distribution from this spike rather than the assumed 75 (per ASM-03's own fallback), or, if the score is meaningless rather than just miscalibrated, drop the confidence gate for a simpler rules-based severity check and escalate everything above Moderate severity to human review regardless of score.

## Result

*(to fill in after the spike runs — blocked on real negotiation runs existing, per ASM-03)*

## Decision

*(to fill in after the spike runs)*
