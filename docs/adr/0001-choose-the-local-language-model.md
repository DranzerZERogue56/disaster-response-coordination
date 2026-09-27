# ADR 0001 — Choose the local language model

- **Status:** Accepted
- **Date:** 2026-09-27
- **Decider:** Dranzer Rogue
- **Requirements affected:** FR-AGENT-01, FR-AGENT-04, FR-INFER-01, NFR-PERF-01, NFR-MNT-01
- **Related ADRs:** none yet (first ADR); constrains future work on FR-COORD tiebreak reasoning quality

## Context

FR-INFER-01 already settles the bigger question here as a Must: all agent reasoning runs entirely on local hardware, zero calls to an external API or cloud model, even if internet is available. NFR-SEC-01 backs this with a measurable check (a connection log showing zero external hosts during a full scenario run). That rules out any hosted API — Anthropic, OpenAI, or otherwise — regardless of quality or cost, which a Week 4 session already worked through when a suggestion of Anthropic's Haiku was corrected against this exact requirement.

So the real decision this week isn't cloud-vs-local. It's which model Ollama serves locally. FR-AGENT-01 requires classifying an incoming report's severity within 5 seconds of intake, and NFR-PERF-01 pins that to a p95 measurement over 20 seeded reports on the target hardware (a 24GB GPU). FR-AGENT-04 adds a ~60-second reasoning timeout before falling back to a non-LLM path — so a model's raw latency matters twice: once for the 5-second classification target, and again for how much margin exists before the more expensive negotiation/reasoning steps hit the 60-second fallback. NFR-MNT-01 also cares here indirectly: a larger model means a longer download during the clean-clone/model-pull step, even though the 5-minute clean-clone test itself explicitly assumes model files are already downloaded.

Two real options were evaluated: `llama3.2:3b` (3B parameters, 2.0GB) and `mistral:7b` (7B parameters, 4.4GB, Apache-2.0). Both run under Ollama and satisfy FR-INFER-01 by construction. The matrix in `docs/tech-evaluation.csv` scores them on latency fit, setup time, license cleanliness, reasoning quality, and existing familiarity.

## Options considered

| Option | Weighted score | The detail that decided it |
|---|---:|---|
| llama3.2:3b | 3.90 | Smallest, fastest option that still clears the 5s classification target with margin; the cost is a non-standard model license and shallower reasoning depth at 3B |
| mistral:7b | 3.60 | Clean Apache-2.0 license and likely stronger tiebreak/negotiation reasoning at 7B, but bigger and slower against the 5s p95 target |

## Decision

We will run **`llama3.2:3b`** via Ollama as the primary local model for agent reasoning. This is the matrix's top-scored option (3.90 vs. 3.60), and the margin is driven mainly by the latency and setup-time criteria that trace directly to NFR-PERF-01 and NFR-MNT-01 — the two criteria with the hardest numeric targets attached to them.

## Consequences

**Positive**

- Smallest, fastest model of the two evaluated, giving the most margin against the FR-AGENT-01 5-second classification target and the FR-AGENT-04 60-second reasoning fallback.
- Smallest download (2.0GB), least likely to be the bottleneck in any clean-clone timing test.

**Negative**

- The model itself ships under a custom, non-OSI "Llama 3.2 Community License" rather than a standard permissive license (MIT/Apache-2.0). At capstone/demo scale this carries no real restriction — the license's own commercial-use clause only triggers above 700 million monthly active users — but it means the license inventory in `docs/tech-evaluation.md` cannot mark every dependency as a clean SPDX permissive license, and this would need re-checking if the project were ever taken toward real deployment. Mitigation: none needed now; re-verify the license text if this project scales past a demo (see revisit trigger).
- 3B parameters gives less reasoning depth than the 7B alternative for the harder judgment calls in FR-COORD's tiebreak logic (severity, then information richness, then reported-first) and the confidence-scoring behind NFR-SEC-02's human-approval gate. Mitigation: NFR-SEC-02 already routes anything under 75/100 confidence to a human, which is exactly the safety net a weaker model needs; if classification or tiebreak quality turns out to be unacceptably shallow in practice, `mistral:7b` is a one-line Ollama model swap behind the same interface, budgeted at roughly 2 hours to re-test and re-benchmark.

## Revisit trigger

Revisit this ADR if the measured NFR-PERF-01 p95 classification latency exceeds 5 seconds on the target hardware once real benchmarking runs (currently unmeasured — ASM-02 in the assumptions log has an end-of-Week-9 verify-by date), or if manual review of classification/tiebreak outputs during Milestone 9-10 testing shows the 75-confidence threshold routing more than 40% of reports to human review (a sign the model's reasoning is too shallow to be useful even with the safety net).

## Verification

| Claim in this ADR | Source | Checked on |
|---|---|---|
| llama3.2:3b: 3B params, 2.0GB pull | https://ollama.com/library/llama3.2 | 2026-09-27 |
| mistral:7b: 7B params, 4.4GB pull, Apache-2.0 | https://ollama.com/library/mistral | 2026-09-27 |
| Llama 3.2 model license: custom "Llama 3.2 Community License," 700M-MAU clause | https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE | 2026-09-27 |
