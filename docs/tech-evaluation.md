# Technology Evaluation — Milestone 5

**Author:** Dranzer Rogue
**Date:** 2026-09-27
**Machine-checkable matrix:** [`docs/tech-evaluation.csv`](tech-evaluation.csv) — passes `tools/score-stack.py`, weights committed in [`b65d1f6`](https://github.com/DranzerZERogue56/disaster-response-coordination/commit/b65d1f6) before scores landed in [`069d481`](https://github.com/DranzerZERogue56/disaster-response-coordination/commit/069d481)

## 1. Architectural drivers

| Driver | Requirement / constraint | Pulls on |
|---|---|---|
| Classify a report's severity within 5 seconds of intake | FR-AGENT-01, measured as NFR-PERF-01 (p95 over 20 seeded reports, 24GB GPU) | LLM model choice |
| All agent reasoning runs locally, zero external API calls, even with internet available | FR-INFER-01, checked by NFR-SEC-01 (zero external hosts in a connection log) | LLM model choice — already forces "local," leaves only "which local model" as a real decision |
| Abandon a reasoning attempt past ~60s, fall back to a non-LLM path | FR-AGENT-04 | LLM model choice (latency margin) |
| Reserve a unit the instant it's proposed and resolve two agents proposing the same unit before either assignment finalizes, with a defined tiebreak | FR-RES-03, FR-COORD-01, FR-COORD-03 | Simulation framework and data store (both sides of the concurrent-write race at the reservation moment) |
| Log every proposal and every dispatcher override; purge both 24h after receipt | FR-AUDIT-01, FR-AUDIT-02, NFR-PRIV-01 | Data store (purge/delete simplicity) |
| Replay a scripted incident sequence at a controlled pace for a reliable demo | FR-SIM-01 | Simulation framework |
| A clean clone reaches a running app in under 5 minutes using only the README | NFR-MNT-01 | All four decisions (setup-time criterion) |
| Survive a simulated 2-minute (0% loss) and 20-minute (≤2% loss) network outage | NFR-REL-03, NFR-REL-04 | Map/routing choice (offline reliability) |

## 2. Weighted evaluation

Full scored matrix: [`tech-evaluation.csv`](tech-evaluation.csv). Summary:

| Decision | Options (2 real each) | Winner | Margin |
|---|---|---|---|
| Local language model | `llama3.2:3b` vs. `mistral:7b` | **llama3.2:3b** — 3.90 | 3.90 vs 3.60 |
| Data store | SQLite vs. PostgreSQL | **SQLite** — 4.40 | 4.40 vs 3.30 |
| Simulation/agent framework | Mesa vs. hand-rolled loop | **Mesa** — 3.95 | 3.95 vs 3.15 |
| Map/routing representation | synthetic location graph vs. OSMnx | **synthetic location graph** — 3.95 | 3.95 vs 3.35 |

No decision fell within the tool's 0.25 "coin flip" margin. Full reasoning, including the one place the matrix's own top-scored criterion pointed the other way (data store — see ADR 0002), is in the individual ADRs: [0001](adr/0001-choose-the-local-language-model.md), [0002](adr/0002-choose-the-data-store.md), [0003](adr/0003-choose-the-simulation-framework.md), [0004](adr/0004-choose-the-map-and-routing-representation.md).

### Sensitivity pass

The closest decision is the local language model (0.30 margin). Its "license cleanliness" criterion (weight 0.20) is the softest one — a policy judgment, not a hard number. Re-running the weighted sum with that weight zeroed out and redistributed to latency (0.30→0.40) and reasoning quality (0.20→0.30) gives `llama3.2:3b` 4.30 vs. `mistral:7b` 3.30 — the gap *widens*, not flips. The decision is not sensitive to how much the license criterion is weighted; it's driven by the latency and setup-time criteria, which trace to hard numeric targets (NFR-PERF-01, NFR-MNT-01), not to a soft one.

## 3. Seam inventory

| # | Seam | Risk | Spike |
|---|---|---|---|
| 1 | LLM output → classification parser (does the model reliably emit a parseable severity + confidence?) | Medium | — |
| 2 | LLM cold-start latency → FR-AGENT-01's 5s classification budget | Medium | — |
| 3 | Mesa negotiation step → SQLite write at the reservation moment (FR-RES-03 / FR-COORD-01) | **High** | [SP-02](spikes/SP-02-sqlite-write-contention-under-concurrent-mesa-agents.md) |
| 4 | LLM confidence score → NFR-SEC-02's 75-point human-approval gate | **High** | [SP-03](spikes/SP-03-llm-confidence-score-calibration.md) |
| 5 | Synthetic location graph → dispatcher's expectation of real geography (FR-MAP-01) | Medium | — |
| 6 | Deferred OSMnx / Overpass API dependency → NFR-REL-03/04 outage simulation | Low (moot while ADR 0004 stands; becomes High again if superseded) | [SP-01](spikes/SP-01-osmnx-real-street-routing.md) (already run) |
| 7 | OSMnx business-name geocoding gap → any future re-integration (found by SP-01, not yet solved) | Medium | [SP-01](spikes/SP-01-osmnx-real-street-routing.md) |

Row 3 isn't hypothetical — it's the exact reason ADR 0002 notes SQLite scored *lower* than PostgreSQL on this one criterion, and it's why that ADR isn't closed on vibes.

## 4. Novelty load

**Count going into this milestone: 4.** Local Ollama model serving, Mesa, OSMnx, and the hand-rolled contract-net negotiation protocol were all simultaneously new — four things to learn at once inside a solo, 240-hour budget.

**Demotion made:** OSMnx is demoted to a deferred upgrade (ADR 0004), bringing novelty load to **3**.

**The remaining 3, defended individually, not just kept by default:**

- **Ollama / local model serving.** Not demotable — it's the mechanism FR-INFER-01 requires and the thing the whole capstone concept depends on. There's no version of this project without it.
- **Mesa.** Kept even though it's new, because the matrix comparison against the alternative (a hand-rolled loop) shows it *reduces* total risk rather than adding to it: the alternative scored worse specifically on the scheduling/data-collection criterion that FR-SIM-01 and FR-COORD need most (2/5 vs. Mesa's 5/5). Learning Mesa's documented API is a bounded cost; inventing an equivalent scheduler from scratch is an open-ended one.
- **Hand-rolled contract-net protocol.** Not demotable — it's the actual subject of the capstone (competing agent teams negotiating over resources), not incidental infrastructure around it.

## 5. Cost sheet (student scale)

| Item | Cost | Fallback |
|---|---|---|
| Ollama, Mesa, SQLite, Python | $0 (all free/open-source, self-hosted) | No vendor tier to lose; if any single package were abandoned upstream, fork it or replace it behind the same interface pattern already used for the LLM (ADR 0001) |
| Local model weights (llama3.2:3b) | $0 (downloaded once, run locally, no per-call fee — required by FR-INFER-01 anyway) | Swap to a smaller/quantized tag if the 24GB GPU is under memory pressure |
| GPU hardware to run the model | One-time, ~$400–$4,000 depending on route chosen (per `HARDWARE.md`'s phased plan) | Smaller local model + CPU inference if hardware acquisition slips |
| GitHub private repo hosting | $0 (within GitHub's free private-repo limits) | Move to a self-hosted git remote if that ever changes |

**Free-tier watch list**

| Service | Free-tier term | Fallback if it changes |
|---|---|---|
| GitHub private repositories | GitHub Free for personal accounts currently allows unlimited private repositories and unlimited collaborators, with a reduced feature set (not a hard quota) | Self-host a git remote if that ever tightens |
| Nominatim geocoding (only relevant if ADR 0004 is superseded and OSMnx is reintroduced) | Public instance: 1 request/second, single-threaded, results must be cached, no reselling | Cache all geocoding results locally on first lookup; self-host a Nominatim instance if the demo needs more throughput |
| Overpass API (only relevant if ADR 0004 is superseded and OSMnx is reintroduced) | Public instances: soft guideline of ~10,000 requests/day and <1GB/day, 512MiB/180s per-request resource cap, HTTP 429 if a request queues past 15s | Cache the pulled street graph to disk after first download (a repeat pull is never needed for one fixed demo town); self-host an Overpass instance for anything heavier |

No paid cloud AI usage exists anywhere in this design — FR-INFER-01 makes that a non-option, not a cost-optimization.

## 6. License inventory

| Dependency | SPDX identifier | Ship/no-ship |
|---|---|---|
| Ollama (runtime) | MIT | Ship |
| `llama3.2:3b` (model weights) | `LicenseRef-Llama3.2-Community` (SPDX's construct for a non-standard license text; not OSI-approved) | Ship — the 700M-MAU commercial clause doesn't reach a capstone demo; monitor if the project is ever productized (see ADR 0001 revisit trigger) |
| Mesa | Apache-2.0 | Ship |
| SQLite | Public domain | Ship |
| OSMnx (deferred, not in the current MVP) | MIT | Ship if/when ADR 0004 is superseded |
| This project's own code | MIT (see [`LICENSE`](../LICENSE), justified in [ADR 0005](adr/0005-choose-the-project-license.md)) | — |

## 7. Verification log

| Claim | Source | Checked on |
|---|---|---|
| Ollama license: MIT | https://github.com/ollama/ollama/blob/main/LICENSE | 2026-09-27 |
| Mesa license: Apache-2.0 | https://github.com/projectmesa/mesa/blob/main/LICENSE | 2026-09-27 |
| OSMnx license: MIT | https://github.com/gboeing/osmnx/blob/main/LICENSE.txt | 2026-09-27 |
| SQLite: public domain | https://sqlite.org/copyright.html | 2026-09-27 |
| `llama3.2:3b`: 3B params, 2.0GB pull | https://ollama.com/library/llama3.2 | 2026-09-27 |
| `mistral:7b`: 7B params, 4.4GB pull, Apache-2.0 | https://ollama.com/library/mistral | 2026-09-27 |
| Llama 3.2 model license: custom, non-OSI, 700M-MAU commercial clause | https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE | 2026-09-27 |
| MIT permits closed-source redistribution with notice preservation only; GPL-3.0-only requires derivative works distributed to the public to also be GPL-3.0 | https://opensource.org/license/mit ; https://www.gnu.org/licenses/gpl-3.0.en.html | 2026-09-27 |
| GitHub Free (personal): unlimited private repos and collaborators, reduced feature set | https://docs.github.com/en/get-started/learning-about-github/githubs-plans | 2026-09-27 |
| Nominatim public-instance policy: 1 req/sec, single-threaded, must cache, no reselling | https://operations.osmfoundation.org/policies/nominatim/ | 2026-09-27 |
| Overpass API public-instance guideline: ~10,000 req/day, <1GB/day, 512MiB/180s per request | https://dev.overpass-api.de/overpass-doc/en/preface/commons.html | 2026-09-27 |

## 8. Known gaps in this submission

Being explicit about what's thin, since Canvas grades the most recent submission and this one is going in on a tight deadline:

- SP-02 and SP-03 are planned but not yet run — both name a concrete decision they'd change if they came back unfavorable.
- The novelty-load defense for Mesa and the contract-net protocol is argued here, not yet measured against a running scenario.
- The Medium- and Hard-tier extra-credit options (a 5th/6th decision, a second run spike, a measured score, a decision memo) are not attempted this submission, given the time available before the deadline. This can change on resubmission — Canvas grades the latest one.
