# Accessibility pass on the documentation (2026-11-22)

Scope: the documents a newcomer or a grader reads first: `README.md`, `docs/runbook.md`, `docs/onboarding.md`, `docs/adr/README.md`, `docs/clean-machine-test.md`, `docs/ci-pipeline.md`, `docs/architecture.md`. The checks run in CI through `tools/check_docs.py` and `tests/unit/test_docs.py`, so a regression fails the build. This is a mechanical pass plus reading; it is **not** a test with a screen reader or a user who relies on one (not done, see the end).

## What was checked and what was found

| Check | Result before this pass | Fix |
|---|---|---|
| One level-1 heading and no skipped heading levels (screen-reader users navigate by headings) | passed in the new documents | none needed; enforced by the check |
| Link text that means something out of context (no "here" or "click here") | passed | none needed; enforced |
| Images have alt text | the new demo GIF in the README has alt text | enforced |
| Diagrams have a text version (a picture of boxes and arrows is invisible to a screen reader) | **failed**: the two Mermaid diagrams, in `docs/architecture.md` section 0 and `docs/ci-pipeline.md`, had no text equivalent | added a "Text version of the diagram" paragraph to each; the check now fails any Mermaid diagram without one |
| Paths and commands the documents mention exist (a reader on a keyboard or a screen reader cannot "just look around" for a missing file) | **failed**: the runbook and onboarding guide named two files that do not exist yet (the Week 14 handoff document and `dependencies.md`) as if they did | reworded to say they are not written yet |
| Plain language and tables with header rows | the tables have header rows; the documents define their terms (`docs/onboarding.md` section 2) | none |
| The animated GIF (motion) | the GIF is 4 frames, 2.6 seconds each, no flashing; every frame carries its caption in text, and section 6 of the README gives the same steps in words | the steps do not depend on the GIF |

## The dispatcher console itself

The console page has its own accessibility record (`docs/performance.md` and `tests/manual/scripts/acc-01-keyboard-only.md`, a keyboard-only pass recorded as self-reported). This pass covers the documents, not the console.

## Not done

- No test with a real screen reader (NVDA, VoiceOver) and no review by a person who uses one.
- No colour-contrast measurement of the rendered Markdown (GitHub controls it).
- The check cannot judge reading level or whether a sentence is clear.
