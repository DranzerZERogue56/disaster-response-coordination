# Definition of Done — Template

Copy this into your repository as `docs/definition-of-done.md` and link it from `README.md`.

## What this is

One checklist. It applies to **every** work item — every card, issue, or task — before
that item may be moved to Done. It is not a plan and it is not per-feature acceptance
criteria; those live with each requirement in `docs/requirements.md`.

## The honesty rule

If you will not do an item every single time, take it off the list. A definition of
done that you routinely skip is worse than no definition of done, because it teaches
you that written commitments are decorative.

Eight to twelve items. Every item must be answerable **yes or no** by someone who is
not you.

---

## The checklist

An item is Done when all of the following are true:

- [ ] It traces to a requirement ID in `docs/requirements.md` (or a new requirement was added and the traceability matrix updated).
- [ ] Every acceptance criterion for that requirement passes, checked by running it — not by reading the code.
- [ ] At least one automated test covers the new behavior, and the whole suite passes locally.
- [ ] The branch is merged only after the pipeline is green on the merge commit.
- [ ] No secret, key, token, or real user data was added to the repository.
- [ ] Error paths are handled: the failure a user is most likely to hit produces a message that names what failed.
- [ ] New user-facing surfaces are keyboard-operable, labeled, and pass the contrast check (or, for a CLI, remain readable with color disabled).
- [ ] Any behavior change a stranger would need to know is reflected in `README.md`, `CHANGELOG.md`, or `docs/runbook.md`.
- [ ] Any use of an AI assistant on this item is recorded in `docs/ai-usage.md`, and every generated line was read and understood.
- [ ] Time spent is written to the hours log the same day.
- [ ] The item was demonstrated once end to end from a clean state, not from the state left over by development.

---

## What a bad definition of done looks like

Keep this next to yours as a warning:

- [ ] It works.
- [ ] Code is clean.
- [ ] Tested.
- [ ] Documented if needed.

Every one of these is unverifiable by anyone but the author, which means the list
enforces nothing. "If needed" is where documentation goes to die.

---

**Adopted:** <YYYY-MM-DD> · **Revised:** <YYYY-MM-DD, with a one-line reason>
