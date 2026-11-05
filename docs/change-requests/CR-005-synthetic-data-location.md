# CR-005 — NFR-SEC-03 names the folders where the synthetic data really lives

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue), 2026-11-05 |
| Date raised | 2026-11-05 |
| Baseline affected | spec-baseline-v1.0, `docs/requirements.md` NFR-SEC-03 (and the data inventory row) |
| Trigger | Milestone 11. NFR-SEC-03 says seeded reports live under one `data/synthetic/` folder. The course layout for Milestone 11 puts generated test data in `tests/data/`, and the demo reports are in `seed/`; nothing was ever put in `data/synthetic/`, so the requirement and the repository disagreed. Ben chose to amend the requirement (decision D3 of the work plan) rather than move the data |

## What changes
Before: "All seeded reports live under one `data/synthetic/` folder, each marked `synthetic: true`; a check script fails on any report file outside that folder or without the marker".
After: "All seeded reports live under `tests/data/` (generated test data) or `seed/` (demo reports and scenarios), each marked `synthetic: true`; a check script (`tools/check_synthetic.py`) fails on any report file outside those folders or without the marker". The data inventory row now names the same two folders. The measure (a check script plus a manual spot-check of 10 random reports) is unchanged.

Not changed on purpose: the historical task text in `docs/plan.md` (T-1.3), `docs/wbs.csv` and the risk register still say `data/synthetic/`; they record what was planned in Week 7.

## Why
A requirement that names a folder nothing lives in cannot be verified, and moving the data would break the course's required test layout. The intent of the requirement (no real incident data, everything marked synthetic) is unchanged and is now checked by a script.

## Impact assessment

| Dimension | Assessment |
|---|---|
| Requirements affected | NFR-SEC-03 (wording of the folder only) |
| Specification sections affected | `docs/requirements.md` non-functional table and data inventory; `docs/architecture.md` traceability row |
| Hours: added / removed | +0.5 / -0 |
| Schedule effect | none |
| Risk effect | none; the check is stricter than before (it now exists) |
| Definition of done effect | none |

## Decision

| Field | Value |
|---|---|
| Decision | approved |
| Decided by | Ben |
| Date | 2026-11-05 |
| Rationale | Ben answered "amend the NFR path". The requirement's intent is intact; only a folder name that was never used changes. A Must requirement's wording moves, so Ben decides whether this counts toward a new baseline tag (spec-baseline-v1.1) |

## Applied

- [x] Specification updated and committed
- [x] Traceability matrix: NFR-SEC-03-AC1 now has automated tests (`tests/unit/test_check_synthetic.py`); the manual spot-check is a separate step Ben performs and records
- [x] Plan and hours re-baselined: not needed (+0.5 h)
- [x] Row added to `CHANGELOG.md`
- [ ] New baseline tag: Ben to decide
