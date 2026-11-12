# CR-011: A local Ollama model as the primary tier of the model chain

> **DRAFT: facts only.** Under the Milestone 12 AI policy the impact analysis and the disposition are Ben's, in Ben's words, with Ben's name and date. The assistant has filled in only what can be looked up (what files change, what tests exist, what was measured). Every cell marked **Ben** is empty on purpose. This CR is not yet in the `CHANGELOG.md` change table; the row is added when Ben writes the disposition.

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue) |
| Date raised | 2026-11-11 |
| Baseline affected | spec-baseline-v1.0: `docs/architecture.md` section 9 (the one external dependency, designed but not wired) and section 5, LLM Generate |
| Trigger | Ben's instruction in the Milestone 12 planning chat on 2026-11-11: build an Ollama client for the local Qwen 3 model, so the third-party failure modes are real and not simulated (question Q64, option A) |

## What changes (facts)
- New `src/classify_propose/ollama_client.py`: an HTTP client for a model server on this machine. Refuses any host but 127.0.0.1, localhost or ::1; follows no redirects; no proxy; refuses replies over 1 MB; hard time cap per call (default 60 s); one retry on an answer of the wrong shape; distinct errors for down, slow, busy (429/503) and changed/malformed responses.
- `src/classify_propose/chain.py` `build_chain()` now reads the environment on every call. `OLLAMA_ENABLED=1` makes the model the primary tier; `OLLAMA_ENABLED=0` or unset is the kill switch (rules tier only, which is the default, so the existing tests never reach a real model). `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_SMALLER_MODEL`, `OLLAMA_TIMEOUT` configure it. All are in `.env.example`.
- One existing rule is narrowed, not removed: `tests/acceptance/test_acceptance_criteria.py` used to forbid any network library in `src/` (support for NFR-SEC-01). It now forbids it everywhere except that one named module, and checks that the module contains the loopback-only check.
- No migration, no change to the data model, no change to the interface of `classify_and_propose`.

## Evidence so far (facts)
- 24 client tests against a stub HTTP server on 127.0.0.1 (`tests/unit/test_ollama_client.py`), 7 wiring tests (`tests/unit/test_chain_wiring.py`), 14 chaos tests through the real intake route (`tests/integration/test_ollama_chaos_http.py`) including the model dying mid-scenario and the kill switch taking effect on the next report.
- One real run against Ben's Ollama (`qwen3:1.7b`, 2026-11-11, this laptop): first call 5.85 s (model load), then 0.86 to 1.16 s. The vague report ("something happened, not sure how bad, no one is answering") was answered Serious / Shelter / confidence 75, which is exactly the auto-dispatch threshold in FR-AGENT-03; the fake rules model scored the same text 40 and held it for a human. **This is a finding about the real model, recorded for the security review and the defect log; it is not fixed.**

## Impact assessment (Ben writes the three lines)

| Line | Ben's words |
|---|---|
| Cost (hours) | **Ben** (the assistant's build time so far: about 2.5 h; Ben's review time: not yet spent) |
| Blast radius | **Ben** (facts for reference: 1 new module, 1 changed module, 1 changed acceptance test, `.env.example`; requirements touched: FR-INFER-01, FR-INFER-02, FR-DEGRADE-02, FR-AGENT-04, NFR-SEC-01, NFR-PERF-01) |
| Risk if done, and risk if not done | **Ben** |

## Decision

| Field | Value |
|---|---|
| Disposition (ACCEPT, REJECT or DEFER, with destination) | **Ben** |
| Decided by | **Ben** |
| Date | **Ben** |
| Rationale | **Ben** |

## Applied
- [x] Code and tests committed (see the commit that adds this file)
- [ ] Disposition written by Ben
- [ ] Row added to the `CHANGELOG.md` change table
- [ ] `docs/architecture.md` section 9 updated (failure-mode table, Milestone 12 work stream 6)
