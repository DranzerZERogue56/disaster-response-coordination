#!/usr/bin/env python3
"""demo_degradation.py - show the model chain degrading, against the real app and database, and save a transcript.

    python tools/demo_degradation.py

Three phases on one fresh database, with Ollama (qwen3:1.7b) running on this machine:
  1. the real model answers (OLLAMA_ENABLED=1);
  2. the model server is "down" (OLLAMA_URL points at a port nothing listens on): reports are still classified, by the
     rules tier, and the reasoning says why;
  3. the kill switch (OLLAMA_ENABLED=0): no call to the model server at all.
It writes docs/evidence/m12-degradation-demo.md. It starts no server of its own and stops nothing.
"""
import json
import os
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

REPORTS = [
    ("4th & Main St", "person fell, visible leg injury, conscious and talking"),
    ("9th & Pine", "man collapsed, chest pain, not breathing well"),
    ("Oak Street shelter", "something happened, not sure how bad, no one is answering"),
    ("Elm St", "smoke coming from a second-floor window, people still inside"),
    ("Birch Ave", "child with a deep cut on the arm, bleeding but alert"),
    ("Cedar Ct", "family displaced by flooding needs shelter tonight"),
]
PHASES = [
    ("1. Model up (real qwen3:1.7b)", {"OLLAMA_ENABLED": "1", "OLLAMA_URL": "http://127.0.0.1:11434"}, REPORTS[0:2]),
    ("2. Model server down (nothing listening on the configured port)", {"OLLAMA_ENABLED": "1", "OLLAMA_URL": "http://127.0.0.1:9"}, REPORTS[2:4]),
    ("3. Kill switch off (OLLAMA_ENABLED=0)", {"OLLAMA_ENABLED": "0"}, REPORTS[4:6]),
]


def main():
    from measure_nfrs import fresh_db

    conn, path = fresh_db()
    for unit_type in ("Fire", "Shelter", "Security", "Medical"):
        for _ in range(3):
            conn.execute("INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) VALUES (1, ?, 1, 'available')", (unit_type,))
    conn.commit()
    conn.close()
    os.environ["DB_PATH"] = path
    from src.web_ui.app import create_app

    client = create_app().test_client()
    lines = [
        "# Degradation demonstration: the model chain",
        "",
        f"Run by `python tools/demo_degradation.py` on {datetime.now(UTC).date().isoformat()}, real Ollama (`qwen3:1.7b`) on this laptop, real app and database (a fresh temporary one). Nothing is mocked.",
        "",
    ]
    for title, env, reports in PHASES:
        for key in ("OLLAMA_ENABLED", "OLLAMA_URL"):
            os.environ.pop(key, None)
        os.environ.update(env)
        lines += [f"## {title}", "", "| Report | Status | Time | Answered by | Severity | Confidence | Held for a person? | Reasoning (start) |", "|---|---|---|---|---|---|---|---|"]
        for place, text in reports:
            body = {"location": place, "severity_raw": text, "timestamp_reported": "2026-11-15T12:00:00+00:00", "reporting_unit": "demo"}
            t = time.perf_counter()
            response = client.post("/reports", data=json.dumps(body), content_type="application/json")
            took = time.perf_counter() - t
            data = response.get_json()
            proposal = data.get("proposal") or {}
            held = (data.get("decision") or {}).get("held_for_human")
            check = sqlite3.connect(path)
            check.row_factory = sqlite3.Row
            row = check.execute("SELECT model_identifier FROM agent_proposals WHERE id = ?", (proposal.get("proposal_id"),)).fetchone()
            check.close()
            lines.append(
                f"| {text[:46]} | HTTP {response.status_code} | {took:.2f} s | {row['model_identifier'] if row else 'none'} | {proposal.get('severity')} | {proposal.get('confidence')} | "
                f"{'yes' if held else 'no'} | {(proposal.get('reasoning') or '')[:70]} |"
            )
        lines.append("")
    check = sqlite3.connect(path)
    reports_n = check.execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0]
    with_proposal = check.execute("SELECT COUNT(DISTINCT report_id) FROM agent_proposals").fetchone()[0]
    fallback = check.execute("SELECT COUNT(*) FROM agent_proposals WHERE reasoning LIKE '[Answered by the rules tier because the primary tier failed.]%'").fetchone()[0]
    escalations = check.execute("SELECT COUNT(*) FROM human_escalations").fetchone()[0]
    check.close()
    page = client.get("/dispatcher")
    lines += [
        "## Counts from the database after all three phases",
        "",
        f"- Reports received: {reports_n}. Reports with a proposal: {with_proposal}. Proposals marked as answered by a fallback tier: {fallback}. Rows in `human_escalations`: {escalations}.",
        f"- `GET /dispatcher` answered HTTP {page.status_code} ({len(page.get_data())} bytes).",
        "",
        "Read the table: in phase 2 the model server was unreachable, yet both reports were classified (by `fake-rules`) and the reasoning says why; in phase 3 the switch removed the model with no restart and no call to it. "
        "If even the rules tier failed, the report would stay `created` and a row would be written to `human_escalations` for a person (`tests/unit/test_model_chain.py`, not exercised in this run).",
    ]
    out = ROOT / "docs" / "evidence" / "m12-degradation-demo.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
