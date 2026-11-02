# Questions for the code reviewer (Milestone 10)

Thanks for looking at this. You do not need to know the project. Each question points at one piece of the main code and asks whether it holds up. Answer in a sentence or two; "I could not tell" is a useful answer too. Please write your answers in the table at the bottom of `iteration-1-self-review.md`, or tell Ben and he will.

How to run it: `./script/setup`, then `./script/seed`, then `./script/test` (55 tests).

The path of one report: `POST /reports` in `src/web_ui/app.py` goes to classify, reserve, decide, notify.

## 1. `src/classify_propose/service.py`: `classify_and_propose`
1. A model's answer is checked by `_validate` before it is trusted. What input could pass that check and still be wrong or dangerous?
2. If the model says "Medical" but no Medical unit is free, the code still proposes one. Is "propose the best remaining unit" the right behaviour, or should it stop?
3. Is it clear from reading only this file how to swap in a different model?

## 2. `src/unit_registry/service.py`: `reserve`, `reserve_for_proposal`, `assign_unit`
4. `reserve` is one UPDATE that only matches `status = 'available'`. Can two requests ever both end up holding unit 1? Why or why not?
5. `release_expired` runs only when someone asks to reserve. What is the worst thing that could happen because it has no timer?
6. `reserve_for_proposal` rewrites the proposal's recommended unit when an alternative wins. Does anything else read the old value and get confused?

## 3. `src/decide_proposal/service.py`: `needs_human`, `decide_auto`, `decide_human`
7. The rule is `confidence < 75 or severity in (Severe, Critical)`. Is there any combination of values that slips through and gets dispatched without a person?
8. `assign_unit` commits, then the proposal row is updated in a second commit. What happens if the program stops between the two?
9. Anyone who can reach `POST /proposals/<id>/decision` can approve. Is the explanation in the self-review (item 4.1) good enough for an iteration, or should it be blocked?

## 4. `src/notify_responder/service.py`: `notify_responder`
10. Notifying only works if the unit is assigned to that approved proposal. Is there a way to get a notification for a unit that should not be told?
11. "Notify" writes a row and nothing else. Is that honest enough as described in the demo and docs?

## 5. Tests and process
12. Pick one test in `tests/` and say what bug it would catch. Is there an obvious bug that no test would catch?
13. Does any commit message in `git log` fail to explain why the change was made?
