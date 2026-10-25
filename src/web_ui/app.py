"""Dispatcher Web UI (docs/architecture.md §3/§5) — walking skeleton.

Serves the one real vertical slice this milestone requires: Submit
Incident Report -> Intake Gateway -> SQLite incident_reports -> a
rendered list a human can see. Every other interface in §5 (Classify &
Propose, Decide Proposal, etc.) is a stub — see docs/skeleton-trace.md
for what's real this week and what isn't.
"""
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.db import connect, ensure_scenario_run
from src.intake_gateway.service import ValidationError, list_reports, submit_report

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def create_app():
    app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

    @app.get("/healthz")
    def healthz():
        conn = connect()
        try:
            conn.execute("SELECT 1").fetchone()
        finally:
            conn.close()
        return jsonify({"status": "ok"})

    @app.get("/reports")
    def reports_index():
        conn = connect()
        try:
            run_id = ensure_scenario_run(conn)
            reports = list_reports(conn, run_id)
        finally:
            conn.close()
        return render_template("reports.html", reports=reports)

    @app.post("/reports")
    def reports_create():
        conn = connect()
        try:
            run_id = ensure_scenario_run(conn)
            fields = request.get_json(silent=True) or request.form
            result = submit_report(conn, run_id, fields)
        except ValidationError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "FIELD_MISSING",
                            "message": str(exc),
                            "field": exc.missing,
                        }
                    }
                ),
                400,
            )
        finally:
            conn.close()
        return jsonify(result), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
