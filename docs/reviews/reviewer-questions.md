# Questions for the code reviewer (Milestone 10)

Thanks for looking at this. You do not need to know the project. Each question points at one piece of the main code and asks whether it holds up. Answer in a sentence or two; "I could not tell" is a useful answer too. Please write your answers in the table at the bottom of `iteration-1-self-review.md`, or tell Ben and he will.

How to run it: `./script/setup`, then `./script/seed`, then `./script/test` (94 tests). Questions 5, 8 and 9 were found in the self-review and already answered by Ben; they are here so you can say whether his answer holds.

The path of one report: `POST /reports` in `src/web_ui/app.py` goes to classify, reserve, decide, notify.

## 1. `src/classify_propose/service.py`: `classify_and_propose`
1. A model's answer is checked by `_validate` before it is trusted. What input could pass that check and still be wrong or dangerous?
2. If the model says "Medical" but no Medical unit is free, the code still proposes one. Is "propose the best remaining unit" the right behaviour, or should it stop?
3. Is it clear from reading only this file how to swap in a different model?

## 2. `src/unit_registry/service.py`: `reserve`, `reserve_for_proposal`, `assign_unit`
4. `reserve` is one UPDATE that only matches `status = 'available'`. Can two requests ever both end up holding unit 1? Why or why not?
5. **(Ben: fixed.)** Expired reservations used to be freed only when someone asked to reserve. There is now a 5-second background clock and a Units table showing when each reserved unit frees. Does that hold up, and is anything about the clock unclear or misleading?
6. `reserve_for_proposal` rewrites the proposal's recommended unit when an alternative wins. Does anything else read the old value and get confused?

## 3. `src/decide_proposal/service.py`: `needs_human`, `decide_auto`, `decide_human`
7. The rule is `confidence < 75 or severity in (Severe, Critical)`. Is there any combination of values that slips through and gets dispatched without a person?
8. **(Ben: fixed.)** Assigning a unit and approving its proposal used to be two separate saves. They are now one transaction, and migration `0002` makes the database refuse an assigned unit whose proposal is not approved. If the program stops at any point, can the two ever disagree?
9. **(Ben: accepted for the demo, to be stated out loud.)** Anyone who can reach `POST /proposals/<id>/decision` can approve, and it always counts as a stand-in dispatcher. Do you agree it is acceptable for an iteration demo, or should it be blocked?

## 4. `src/notify_responder/service.py`: `notify_responder`
10. Notifying only works if the unit is assigned to that approved proposal. Is there a way to get a notification for a unit that should not be told?
11. "Notify" writes a row and nothing else. Is that honest enough as described in the demo and docs?

## 5. Tests and process
12. Pick one test in `tests/` and say what bug it would catch. Is there an obvious bug that no test would catch?
13. Does any commit message in `git log` fail to explain why the change was made?

## 6. Added later (slices 6 and 7, and the database rule)
14. `src/intake_gateway/queue.py`: while offline, reports are saved as `queued` and processed oldest-first on reconnection, ordered by the reported time as text. What input would put them in the wrong order, or lose one?
15. `src/override_assignment/service.py`: an override needs a reason and is one transaction (unit swap, proposal marked `modified`, log row). Can a half-done override ever be left behind? Is it clear who did what, when and why from the log row alone?
16. `migrations/0002-assigned-requires-approved.sql`: three triggers say an assigned unit needs an approved (or modified) proposal. Is there a way around them, or a case where they block something legitimate?

## Answers (peer reviewer, relayed by Ben, 2026-11-01)

Note on matching: the reviewer sent 15 numbered answers for 16 questions, so they were matched to questions by what each answer says. Q5 and Q8 are the two "already fixed" answers (matched in order); Q6 is the "No, it does not" answer; Q9 (no login) has no answer. The reviewer should confirm Q5, Q6, Q8 and Q9 if the exact match matters.

| Q | Answer |
|---|---|
| 1 | Any data could technically be input and pass; the check should only validate shape. Answers that come back and pass validation are more likely to be correct, and prompt engineering can improve accuracy further. |
| 2 | "Propose the best remaining unit" is correct. The system needs to offer at least an option. |
| 3 | It is clear. |
| 4 | No. That was worked on in an earlier slice (one conditional UPDATE, plus the eight-thread test). |
| 5 | (see note) "He already fixed it." |
| 6 | No, it does not. |
| 7 | No. Nothing should get dispatched without a person, and nothing does. |
| 8 | (see note) "Ben already fixed it." |
| 9 | (no answer given) |
| 10 | The dispatcher can always notify them outside the software, but there should be a way to do it in the software. |
| 11 | That is honest enough. |
| 12 | There are no obvious bugs that a test would not catch. |
| 13 | No. |
| 14 | Reports being entered with a different time, so not UTC. |
| 15 | I do not believe a half-done override could ever be left behind. |
| 16 | There should be no way they block something legitimate. |

