# CR-014: Several or larger locally hosted models, and the target-hardware work (REJECT)

> **DRAFT expanded from Ben's own words.** The disposition is Ben's; the assistant widened it with facts from the repo. Text added beyond Ben's meaning is marked **(assistant, Ben to confirm)**. Ben will rewrite it. The three impact lines are left for Ben.

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue) |
| Date raised | 2026-11-15 |
| Baseline affected | spec-baseline-v1.0: the requirements that name a 24 GB GPU (RTX 3090/4090) and a local model: FR-INFER-02, NFR-PERF-01; `docs/architecture.md` section 9 (a primary model plus a smaller model) |
| Trigger | Reviewing CR-011 (the Ollama client): whether to host several models, or models large enough for the specified hardware |

## What would have changed (facts, assistant)
- Several locally hosted models would mean using the second ("smaller") tier of the fallback chain with a separately hosted model, and larger primary models. The client already supports a second model as an optional setting (`OLLAMA_SMALLER_MODEL`), which is empty by default.
- This laptop (measured 2026-11-15): Intel Core i5-12450H, 63.7 GB RAM, NVIDIA GeForce GTX 1650 (video memory not measured). The requirements name a 24 GB RTX 3090 or 4090. Models present on the machine: `qwen3:1.7b` (about 1.4 GB), `phi4-mini` (about 2.5 GB), `smollm2:360m` (about 0.7 GB).
- FR-INFER-02 and NFR-PERF-01 already stay "unverified on target hardware" in the test plan (section 2) and in `docs/rc-exit-criteria.md` line 1. Rejecting this change does not move those two; it records why.

## Ben's disposition (expanded from his words)

| Field | Value |
|---|---|
| Disposition | **REJECT** |
| Decided by | Ben (Dranzer Rogue) |
| Date | 2026-11-15 (draft date; Ben to confirm) |
| What is accepted instead | One demo model right now, `qwen3:1.7b`, which this laptop can host. |
| Rationale | I cannot host models big enough to justify several of them or a large one, so I am rejecting the hardware-target sections in exchange for something feasible. The rest of the model work I accept (CR-011). |
| Reversal | Rejected, not deferred. It would be reopened only if suitable hardware becomes available **(assistant, Ben to confirm)** |

## Impact assessment (Ben writes the three lines)

| Line | Ben's words |
|---|---|
| Cost (hours) | **Ben** |
| Blast radius | **Ben** (facts above) |
| Risk if rejected, and risk if accepted | **Ben** |

## Point settled by Ben on 2026-11-15
On 2026-11-12 Ben asked for `smollm2:360m` as a smaller second tier. That fits "one demo model" only if the second tier stays a disabled option. **Ben's decision (2026-11-15, in chat, to be rewritten in his words): it stays as a disabled option** (`OLLAMA_SMALLER_MODEL`, empty by default; it was a one-time-use model).

## Ben's notes as written (verbatim, 2026-11-15)

> I'm rejecting using multiple local hosted models in exchange for 1 demo model right now, as I cannot host big enough models, so we are rejecting the hardware sections in exchange for something more feasible. But I'm accepting most of the other items currently.

## Applied
- [ ] Ben rewrites and confirms
- [ ] Row in the `CHANGELOG.md` change table
- [ ] Marked in `docs/requirements.md` where FR-INFER-02 and NFR-PERF-01 name the target hardware (with date and this CR)
