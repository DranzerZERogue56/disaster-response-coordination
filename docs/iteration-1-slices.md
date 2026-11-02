# Iteration 1 slice log (Milestone 10)

One section per slice, written when the slice lands. Evidence, not claims.
"Confidence" is Ben's own rating after he has looked at the slice: a number
0-100 and a colour (Green = I can explain every line and I watched it work;
Amber = it works but I have gaps; Red = I don't trust it yet).

Model note: all slices run on the rules-based fake model until Ollama is
wired in. Switching is one setting (`CLASSIFY_MODEL`), no code changes.

## Slice 1: Classify & Propose

| Item | Evidence |
|---|---|
| Requirements | FR-AGENT-01 (severity within 5 s, escalate if not confident), FR-AGENT-02 (proposal with unit, confidence, reasoning, alternatives) |
| Where it lives | `src/classify_propose/model.py` (swappable model, `FakeModel`), `src/classify_propose/service.py` (`classify_and_propose`), hook in `src/web_ui/app.py` (`POST /reports`) |
| Acceptance criteria | AC-1 a created report gets a severity and a proposal with all four parts. AC-2 a model answer that fails validation is never trusted: the report stays `created` for a human. AC-3 with no free unit it still proposes the best remaining one (out-of-service units are excluded) |
| Tests | `tests/test_classify_propose.py`: clear report, vague report (confidence 40, under 75), out-of-service unit skipped, invalid model output, no unit of needed type, unknown report. 9 of 9 pass locally with the intake tests |
| Handled failure path | `ClassifyError` codes `MODEL_OUTPUT_INVALID`, `NO_UNIT_OF_TYPE`, `REPORT_NOT_FOUND`; the route returns `needs_human` instead of a proposal |
| Seed data | `seed/iteration-1.sql` (one run, one Medical node, two Medical units) |
| Commit | `bd53194` |
| Not done | Reserving the unit (slice 2). Deciding or escalating by confidence (slices 3-4). Real model (Ollama main, Python-side fallback). The 5 s timing is not measured yet (fake model is instant) |
| Ben's confidence | ____ / 100, colour: ____ |
