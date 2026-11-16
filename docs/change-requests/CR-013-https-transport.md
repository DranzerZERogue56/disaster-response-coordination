# CR-013: Move the app and the model connection from HTTP to HTTPS (DEFER)

> **DRAFT expanded from Ben's own words.** The disposition is Ben's; the assistant widened it with facts from the repo. Text added beyond Ben's meaning is marked **(assistant, Ben to confirm)**. Ben will rewrite it. The three impact lines are left for Ben.

| Field | Value |
|---|---|
| Raised by | Ben (Dranzer Rogue) |
| Date raised | 2026-11-15 |
| Baseline affected | spec-baseline-v1.0; `docs/security-review.md` area 5 (transport); `docs/architecture.md` section 9 |
| Trigger | Reviewing CR-011 (the Ollama client), Ben disagreed that everything currently speaks plain HTTP and not HTTPS |

## What would change (facts, assistant)
- Today the dispatcher app serves plain HTTP on 127.0.0.1:8080 (`script/start`), and the Ollama client talks plain HTTP to a model server on this machine. `src/classify_propose/ollama_client.py` refuses any URL that is not `http` to 127.0.0.1, localhost or ::1 (`_check_local`), and a test pins that (`test_it_refuses_to_talk_to_anything_but_this_machine_over_plain_http`, which lists `https://127.0.0.1:11434` as refused).
- A move to HTTPS would touch: that one function and its tests, the acceptance guard that checks the loopback rule, the app's start command, and a certificate (a self-signed one for localhost). Ollama itself serves plain HTTP, so TLS on that leg would normally be added in front of it with a proxy **(assistant, Ben to confirm)**.
- Traffic today never leaves this machine, because the client refuses every other host. That is a fact for Ben's risk line, not a conclusion.

## Ben's disposition (expanded from his words)

| Field | Value |
|---|---|
| Disposition | **DEFER** |
| Destination | The next build period, about two weeks from 2026-11-15 (roughly the week of 2026-11-29, Milestone 14), as backlog item **B-11** in `docs/backlog.md` (id assigned when the backlog is final) |
| Decided by | Ben (Dranzer Rogue) |
| Date | 2026-11-15 (draft date; Ben to confirm) |
| Rationale | This is a big change, not a tweak, and I do not want to rush it into the release candidate. The next period is when most of the building happens. Because the model is reached through one small function, I expect to make a clean swap then. |

## Impact assessment (Ben writes the three lines)

| Line | Ben's words |
|---|---|
| Cost (hours) | **Ben** |
| Blast radius | **Ben** (facts above) |
| Risk if done now, and risk if deferred | **Ben** |

## Ben's notes as written (verbatim, 2026-11-15)

> He somewhat tweaked and disagreed, especially with the fact that we're only using HTTP instead of HTTPS right now.
>
> That needs to be a big change that I need to defer with the destination, probably to 2 weeks from now, where we start doing most of the building. I can make a clean swap.

## Applied
- [ ] Ben rewrites and confirms
- [ ] Row in the `CHANGELOG.md` change table
- [ ] Item added to `docs/backlog.md` (B-11) with its estimate and acceptance criteria
- [ ] Listed in `docs/security-review.md` area 5 as an accepted, deferred finding
