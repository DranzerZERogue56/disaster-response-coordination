# CR-012: Retroactive record of the three Milestone 7 deferrals

> **DRAFT: facts only.** This records a decision that was made on 2026-10-10, before baseline v1.0 (2026-10-18), and was never filed as a change request. The assistant has filled in only what can be looked up in the repo. Every cell marked **Ben** is empty on purpose: the impact analysis and the disposition are Ben's, in Ben's words, with Ben's name and date. This CR is in the `CHANGELOG.md` change table as "pending Ben", not as approved.

| Field | Value |
|---|---|
| Raised by | **Ben** |
| Date raised | **Ben** (drafted by the assistant on 2026-11-15) |
| Baseline affected | spec-baseline-v1.0 (the requirements below already carried their Won't status when the baseline was declared) |
| Trigger | The Milestone 7 scope decision of 2026-10-10 (`docs/plan.md` section 7): the plan was 14.1 h over plannable capacity after re-estimation and a capacity increase, and six tasks were deferred. Three of them move a requirement from Should to Won't (this release). Release-candidate exit criterion 9 (`docs/rc-exit-criteria.md`) asks that every cut requirement carry a CR reference. |

## What changes (facts)

| Requirement | Before | After | Task and hours recovered (`docs/plan.md` section 7) | Backlog |
|---|---|---|---|---|
| FR-INTAKE-03 Duplicate report detection | Should | Won't (this release) | T-3.3, 4.17 h | B-01 |
| FR-INFER-03 Hardware capability check | Should | Won't (this release) | T-2.1b, 1.17 h | B-02 |
| FR-MAP-01 Zone boundary display | Should | Won't (this release) | T-10.2 and T-12.4 together, 4.17 h | B-03 |

- The "Scope decision" line under each requirement in `docs/requirements.md` states the reason and now also carries a Status line pointing here and to the backlog item. No other requirement text was changed; the acceptance criteria are untouched.
- `docs/requirements.md` change log, version 1.3 (2026-10-10): "FR-INTAKE-03, FR-INFER-03, and FR-MAP-01 moved from Should to Won't (this release), each with a scope-decision note".
- Two other tasks deferred on the same day (T-11.2, T-11.3) cut test coverage, not requirements, and are not part of this CR.
- FR-INTAKE-03-AC1/AC2 have no test (`docs/traceability.csv`). FR-INFER-03 and FR-MAP-01 still have `TODO` placeholders for their acceptance criteria.

## Why (facts from the record)
The three Won't moves closed part of a 14.1 h gap (`docs/plan.md` section 7). The recorded reasons are: a failed model load still surfaces an error through FR-DEGRADE-02's fallback chain (FR-INFER-03); the `incident_reports` table already supports duplicates through `duplicate_of_id` (FR-INTAKE-03); FR-MAP-01's own rationale named it as the first thing to slip (FR-MAP-01).

## Impact assessment (Ben writes it)

| Dimension | Assessment |
|---|---|
| Requirements affected | **Ben** (facts for reference: FR-INTAKE-03, FR-INFER-03, FR-MAP-01) |
| Specification sections affected | **Ben** (facts for reference: the three requirement entries and the version 1.3 change-log row in `docs/requirements.md`) |
| Hours: added / removed | **Ben** (facts for reference: 9.51 h of deferred work in total, 4.17 + 1.17 + 4.17, from `docs/plan.md` section 7) |
| Schedule effect | **Ben** |
| Risk effect | **Ben** |
| Definition of done effect | **Ben** |

## Decision

| Field | Value |
|---|---|
| Decision | **Ben** |
| Decided by | **Ben** |
| Date | **Ben** |
| Rationale | **Ben** |

## Applied

- [x] Status line added to each of the three requirements in `docs/requirements.md`
- [x] Backlog items B-01, B-02, B-03 written in `docs/backlog.md` (proposed by the assistant; dispositions are Ben's)
- [ ] Impact analysis and disposition written by Ben
- [ ] Traceability matrix reviewed by Ben
- [x] Row added to `CHANGELOG.md` (as "pending Ben")
- [ ] New baseline tag: not applicable unless Ben decides a Must requirement moved (none of the three is Must)
