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

> **Expanded from Ben's own notes (kept word for word at the bottom of this file).** The assistant only widened Ben's sentences with facts from the repo; the choices are Ben's. Text the assistant added beyond Ben's meaning is marked **(assistant, Ben to confirm)**. Ben will rewrite this section in his own words.

| Field | Value |
|---|---|
| Disposition (ACCEPT, REJECT or DEFER, with destination) | **ACCEPT, with two parts carved out and recorded as their own change requests:** the move to HTTPS is **DEFERRED** (CR-013, destination: the build period about two weeks from 2026-11-15, roughly the week of 2026-11-29, backlog item B-11), and the use of several or larger locally hosted models, with the target-hardware work, is **REJECTED** (CR-014) in favour of one demo model. |
| Decided by | Ben (Dranzer Rogue) |
| Date | 2026-11-15 (draft date; Ben to confirm) |
| Rationale | I accept almost all of what this change request builds: the Ollama client, the fallback-chain wiring with the kill switch (`OLLAMA_ENABLED`), the configuration variables, and the narrowing of the "no network library in `src/`" test to the one local-only module. I disagree on two points. (1) The client and the app speak plain HTTP, not HTTPS. I do not want to rush a transport change into a release candidate; it is a bigger change that fits the next build period, and because the model is reached through one small function I expect a clean swap later (CR-013). (2) I will not pursue several locally hosted models or bigger ones. My laptop cannot host models big enough to matter, so I am trading the hardware-target sections for something feasible: one demo model, `qwen3:1.7b` (CR-014). |

### What "accept almost all" covers (facts, assistant)
- Accepted as built: `src/classify_propose/ollama_client.py`; the `build_chain()` wiring and kill switch in `src/classify_propose/chain.py`; the five environment variables in `.env.example`; the narrowed acceptance test; 45 new tests (24 client, 7 wiring, 14 chaos) and the whole suite at 595 passed when committed (`d8d0bcb`).
- Accepted with a safeguard added afterwards: DEF-029 (a real model scored a vague report at exactly the auto-dispatch bar of 75). Answers from a real model now need confidence 85 or more (`MODEL_AUTO_APPROVE_MIN`, never below 75) before a unit is dispatched without a person. The 85 is a provisional number picked by the assistant because Ben gave none **(assistant, Ben to confirm)**.

### Point of tension to settle **(assistant, Ben to confirm)**
Ben's notes reject "multiple local hosted models", but on 2026-11-12 Ben also asked for `smollm2:360m` as a smaller second tier. The code supports an optional second model (`OLLAMA_SMALLER_MODEL`, empty and therefore off by default). Ben to say which it is: keep it as a disabled option, or remove it from `.env.example` and the chain wiring.

## Applied
- [x] Code and tests committed (see the commit that adds this file)
- [x] Disposition drafted by Ben (notes below), expanded by the assistant, Ben to rewrite and confirm
- [ ] Row added to the `CHANGELOG.md` change table
- [ ] `docs/architecture.md` section 9 updated (failure-mode table, Milestone 12 work stream 6)

## Ben's notes as written (verbatim, 2026-11-15)

> For disposition, Ben accepted almost all of them. He somewhat tweaked and disagreed, especially with the fact that we're only using HTTP instead of HTTPS right now.
>
> That needs to be a big change that I need to defer with the destination, probably to 2 weeks from now, where we start doing most of the building. I can make a clean swap.
>
> I'm rejecting using multiple local hosted models in exchange for 1 demo model right now, as I cannot host big enough models, so we are rejecting the hardware sections in exchange for something more feasible. But I'm accepting most of the other items currently.
