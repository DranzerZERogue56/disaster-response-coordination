# Specification Baseline v1.0

**Declared:** 2026-10-18
**Declared by:** Dranzer Rogue, author and moderator of record
**Review report:** `docs/review/design-review-checklist.md`, `docs/review/review-defect-log.csv`

## Artifacts frozen at this baseline

| Artifact | Repo path | Version | State at freeze |
|---|---|---|---|
| Project charter | `docs/charter.md` | 1.0 | approved |
| Scoping decision | `docs/scoping-decision.md` | 1.0 | approved |
| Requirements specification | `docs/requirements.md` | 1.3 | approved with rework (DR-002, DR-006, DR-007) |
| Technical specification | `docs/architecture.md` | v0.1 | approved |
| Architecture decision records | `docs/adr/0001`–`0006` | current | approved |
| Technology evaluation | `docs/tech-evaluation.md`, `docs/tech-evaluation.csv` | current | approved |
| Work breakdown and schedule | `docs/plan.md` | v1.0 | approved with rework (gap closed 2026-10-10) |
| Risk register | `docs/risk-register.md` | current | approved with rework (DR-005, R-10 added) |
| Definition of done | `docs/definition-of-done.md` | current | approved with rework (DR-003, DR-004) |
| Traceability matrix | `docs/traceability.csv` | current | approved with rework (DR-001) |

## Open items carried past the baseline

| Id | Description | Disposition | Due |
|---|---|---|---|
| DR-005 | R-10 (Flask/Web UI novelty risk) needs a Likelihood/Impact score from the author | Open — scoring is the author's call, not drafted here | Week 9, before WP-7 starts |
| DR-006 | ASM-01 (GPU hardware availability) verify-by date was already overdue at review time; needs the author's real answer about hardware status | Open | 2026-10-21, before Milestone 9 construction starts |

## What this means from today

Everything in the table above changes only through a change request (`docs/change-requests/`). Code does not exist yet — this baseline is entirely documentation and design, which is the correct state for a Week 8 checkpoint in this course. Typos, clarifications that don't change meaning, and formatting stay ordinary commits; anything crossing the threshold rule in `docs/change-requests/CR-000-template.md` gets a numbered CR and a row in `CHANGELOG.md`.
