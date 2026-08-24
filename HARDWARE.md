# Hardware — Local Agent/Model Server

In-house GPU server for running Ollama and local LLMs, so the resource
agents, incident-command agent, and multi-agent negotiation can run
on-premises (cost savings + full control over models) instead of a paid
API. Acquired incrementally across the semester — see **Calendar
alignment** below for when each piece needs to actually be ready, tied to
[`CALENDAR.md`](CALENDAR.md) and the build phases in
[`PROJECT.md`](PROJECT.md).

## Core Components

| Component | Spec | Cost |
|---|---|---|
| GPU | RTX 4090 (24GB) or used RTX 3090 (24GB) | $1,500–2,500 |
| System RAM | 48GB DDR5 | $250–400 |
| CPU | Ryzen 7 7700X or comparable 8-core | $250–400 |
| Motherboard | PCIe 4.0/5.0 capable | $150–250 |
| Storage | 2TB NVMe SSD | $100–150 |
| PSU | 1000W+ (GPU power hungry) | $150–200 |
| Case + Cooling | Standard PC case | $100–200 |

**Total:** ~$2,500–4,000 new, ~$1,800–2,500 used

## Remote Access Setup

- **Host server**: runs Ollama + API wrapper, exposed on local network (or
  Ngrok for external access)
- **Client devices**: laptop/phone access via REST API or WebSocket
  connection
- **Network**: Ethernet to server preferred (WiFi works but adds latency
  to token streaming)

## Phased Approach

- **Phase 1**: Buy hardware, install Ubuntu/Linux, set up Ollama with 2–3
  test models locally
- **Phase 2**: Expose Ollama API on the home network (default
  `localhost:11434`)
- **Phase 3**: Connect from laptop/phone via HTTP requests to that API
  endpoint

**Stop condition**: can spawn 2 concurrent agent instances + access from a
remote device with <500ms latency.

## Calendar alignment

The project's LLM backend (see `PROJECT.md`) is Ollama-first behind a
swappable interface — so real negotiation/policy code can't run for real
until this hardware exists. Map phases to the weeks that actually need
them:

| Week | Dates | What's being built | Hardware needed by then |
|---|---|---|---|
| 2–3 | Aug 31–Sep 13 | Early throwaway negotiation prototype (validates NL bidding feasibility per `RISKS.md` #2) | None required — prototype on existing laptop/dev machine with any small local model, just to sanity-check the approach before hardware exists |
| 9 | Oct 19–25 | Mesa scenario engine + CI skeleton (Walking Skeleton) | **Phase 1 complete**: server built, Ubuntu installed, Ollama running with 2–3 test models — so the walking skeleton can make a real (if trivial) call to the local LLM |
| 10 | Oct 26–Nov 1 | Resource agents + contract-net negotiation, real LLM bidding | **Phase 2 + stop condition met**: API exposed on network, 2 concurrent agent instances working with <500ms latency — this is the week negotiation actually needs multiple agents calling the LLM at once |
| 11 | Nov 2–8 | Incident-command LLM policy layer + disruption injection | Concurrency load increases (command agent + all resource agents now querying Ollama) — confirm the server holds up under this before locking the SDD assumptions further |
| 13 | Nov 16–22 | Dashboard (React + Leaflet) + OSMnx | **Phase 3**: remote access from laptop/phone — develop and view the live dashboard from a client device while the server does the heavy simulation/inference work |
| 14 | Nov 23–29 | Full evaluation runs (5–10 runs/condition) | Sustained concurrent load over many scenario repeats — the real stress test of the hardware, not just a single demo run |
| 15 | Nov 30–Dec 6 | Live-demo rehearsal | Confirm remote-access latency from wherever the actual presentation happens (podium/laptop) to the home server, not just from the same room |

If hardware acquisition slips behind this table, fall back to the
Ollama-on-existing-machine path (smaller/quantized model, no dedicated
GPU) rather than blocking the week's build item — the swappable LLM
backend interface exists specifically so this degradation doesn't require
a rewrite.
