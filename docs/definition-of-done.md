# Definition of Done — Disaster Response Coordination

Baselined 2026-10-18 alongside `docs/requirements.md` v1.3 (see `docs/baseline.md`). Changes to the checklist itself go through `docs/change-requests/` per the threshold rule (item 5: "changes the definition of done").

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
- [ ] No secret, key, token, or real user data was added to the repository.
- [ ] Error paths are handled: the failure a user is most likely to hit produces a message that names what failed.
- [ ] New user-facing surfaces are keyboard-operable, labeled, and pass the contrast check (or, for a CLI, remain readable with color disabled).
- [ ] Any use of an AI assistant on this item is recorded in `docs/ai-usage.md`, and every generated line was read and understood.
- [ ] The item was demonstrated once end to end from a clean state, not from the state left over by development.
- [ ] The week's hours are logged in `docs/hours-log.csv` before that week's milestone is submitted.

---

## What I cut from the template, and why

This is an MVP being built to prove the concept, so three template items came off the list. Each one is something I would skip every time right now:

- **"The branch is merged only after the pipeline is green on the merge commit."** CI does not exist until Milestone 9, and I am a solo developer committing straight to `main` during the MVP. Revisit when CI is running.
- **"Any behavior change a stranger would need to know is reflected in `README.md`, `CHANGELOG.md`, or `docs/runbook.md`."** Still cut for per-item Done checks: `docs/runbook.md` doesn't exist yet (Week 13, the documentation milestone). **Update, 2026-10-18 (DR-001, this week's design review):** `CHANGELOG.md` itself does now exist as of this week's baseline, but it serves a narrower purpose than this cut item implies — it tracks *specification* changes via `docs/change-requests/` (`docs/baseline.md`'s change-control process), not general behavior changes per work item. The full per-item changelog habit this bullet describes is still deferred to Week 13.
- **"Time spent is written to the hours log the same day."** My hours log is updated in weekly batches, so I would skip this every time. In its place I added a weekly version as the last checklist item: the week's hours are logged before that week's milestone is submitted.

Nine items remain (eight kept from the template, plus the weekly hours-log item). Each one is answerable yes or no by someone who is not me.

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

**Adopted:** 2026-09-20 · **Revised:** not yet
