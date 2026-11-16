# Degradation demonstration: the model chain

Run by `python tools/demo_degradation.py` on 2026-11-16, real Ollama (`qwen3:1.7b`) on this laptop, real app and database (a fresh temporary one). Nothing is mocked.

## 1. Model up (real qwen3:1.7b)

| Report | Status | Time | Answered by | Severity | Confidence | Held for a person? | Reasoning (start) |
|---|---|---|---|---|---|---|---|
| person fell, visible leg injury, conscious and | HTTP 201 | 10.20 s | ollama/qwen3:1.7b | Moderate | 85 | no | The person is conscious and talking, indicating a non-emergency situat |
| man collapsed, chest pain, not breathing well | HTTP 201 | 1.23 s | ollama/qwen3:1.7b | Severe | 95 | yes | The report indicates a man collapsed with chest pain and not breathing |

## 2. Model server down (nothing listening on the configured port)

| Report | Status | Time | Answered by | Severity | Confidence | Held for a person? | Reasoning (start) |
|---|---|---|---|---|---|---|---|
| something happened, not sure how bad, no one i | HTTP 201 | 2.24 s | fake-rules | Moderate | 40 | yes | [Answered by the rules tier because the primary tier failed.] No recog |
| smoke coming from a second-floor window, peopl | HTTP 201 | 2.09 s | fake-rules | Serious | 75 | no | [Answered by the rules tier because the primary tier failed.] Matched  |

## 3. Kill switch off (OLLAMA_ENABLED=0)

| Report | Status | Time | Answered by | Severity | Confidence | Held for a person? | Reasoning (start) |
|---|---|---|---|---|---|---|---|
| child with a deep cut on the arm, bleeding but | HTTP 201 | 0.04 s | fake-rules | Serious | 75 | no | Matched 1 Medical keyword(s) in the report text. |
| family displaced by flooding needs shelter ton | HTTP 201 | 0.04 s | fake-rules | Moderate | 95 | no | Matched 3 Shelter keyword(s) in the report text. |

## What the dispatcher sees

`GET /dispatcher` returned 9611 characters of HTML after all three phases; every report in phases 2 and 3 appears there with its proposal, so none was lost. Each proposal made by a fallback tier carries a reasoning that starts with `[Answered by the rules tier because the primary tier failed.]`.

Read the table: in phase 2 the model server was unreachable, yet both reports were classified (by `fake-rules`); in phase 3 the switch removed the model with no restart. If even the rules tier failed, the report would stay `created` and a row would be written to `human_escalations` for a person (`tests/unit/test_model_chain.py`).
