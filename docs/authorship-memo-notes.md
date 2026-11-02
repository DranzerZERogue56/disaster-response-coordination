# Authorship Memo: Ben's answers so far (NOTES, not the memo)

**These are Ben's answers to the memo prompts, recorded 2026-11-01 so they are not lost. The memo itself (2 to 3 pages, to whoever inherits this repository) must be written by Ben in his own words; this file is not a draft of it.** The Hard tier is graded on honesty, specificity and self-awareness. The AI-usage log says the assistant wrote the code, so a memo the assistant wrote would defeat its purpose.

| Prompt | Ben's answer (his words where quoted) |
|---|---|
| Most assistant-shaped file | `src/classify_propose/model.py` (the fake model's keyword lists) |
| Defend it as your work or admit it is not yet | Defend it as his work |
| Design decisions that were his | Reservation as its own module; `decided_by = 'auto'` versus the dispatcher id; the database rule ("if it's assigned it's approved"); the 4-minute window and the visible clock; the stand-in dispatcher, stated out loud in the demo. Calls he describes as "50/50": fake model now with Ollama later |
| Specific changes he made himself | None to the code. "I just had it make the revisions that I might have made myself" |
| Tests that prove it works | The safety-rule table (74, 75, 90, Severe, Critical); the 10-reports-0-lost outage test; the direct-SQL tests against the database triggers |
| The 2 a.m. question | First re-run the tests and the secrets check and, if needed, roll back to the `iteration-1` tag; then look at `/units` and `/proposals/pending` for the current state |
| One place he accepted output he cannot explain | None |
| Explain it or rewrite it | Neither yet: "it doesn't exist" (because of the answer above) |
| Whose work is this, and what makes that true | "Mine": he decided what to build, how it should behave, and what counts as done |
| One real gap he will admit | There is no login yet |
| Unassigned reply | "B. To a degree." Ben to say which prompt this answers |

**Things the memo will be checked against (for Ben, not for copying):** the AI-usage log says the assistant wrote all of the code and that Ben read the service files for slices 1-3, and `decide_human`, `notify_responder` and the tests for slices 4 and 5. He has not stated reading slices 6 and 7 or the database triggers. "None" for an unexplained thing is a strong claim; the sweeper thread, the transaction handling and the trigger SQL (the `COALESCE` for NULL) are the places a reader is most likely to ask. A memo that admits one real gap and shows a plan scores higher than one claiming none.
