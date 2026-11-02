"""Dispatcher Web UI (docs/architecture.md §3/§5) — walking skeleton.

Serves the one real vertical slice this milestone requires: Submit
Incident Report -> Intake Gateway -> SQLite incident_reports -> a
rendered list a human can see. Every other interface in §5 (Classify &
Propose, Decide Proposal, etc.) is a stub — see docs/skeleton-trace.md
for what's real this week and what isn't.
"""
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.classify_propose.model import get_model
from src.classify_propose.service import ClassifyError, classify_and_propose
from src.db import connect, ensure_scenario_run
from src.decide_proposal.service import (
    DecideError,
    decide_auto,
    decide_human,
    list_pending,
    stub_dispatcher_id,
)
from src.intake_gateway.service import ValidationError, list_reports, submit_report
from src.unit_registry.service import RegistryError, reserve_for_proposal

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
            # Architecture §5: creating a report triggers Classify & Propose.
            # If it can't classify, the report stays 'created' for a human.
            try:
                result["proposal"] = classify_and_propose(
                    conn, result["report_id"], get_model()
                )
            except ClassifyError as exc:
                result["proposal"] = None
                result["needs_human"] = {"code": exc.code, "message": str(exc)}
            # Slice 2: reserve the proposed unit the moment it is proposed.
            # Its own call (not inside classify) so it can fail on its own.
            if result["proposal"]:
                try:
                    result["reservation"] = reserve_for_proposal(
                        conn, result["proposal"]["proposal_id"]
                    )
                    # Slice 3: auto-approve if the safety rule allows it;
                    # otherwise it waits for a human (slice 4).
                    result["decision"] = decide_auto(
                        conn, result["proposal"]["proposal_id"]
                    )
                except RegistryError as exc:
                    result["reservation"] = None
                    result["error"] = {
                        "code": exc.code,
                        "message": str(exc),
                        "tried": exc.tried,
                    }
                    return jsonify(result), 409
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

    @app.get("/proposals/pending")
    def proposals_pending():
        conn = connect()
        try:
            return jsonify({"pending": list_pending(conn)})
        finally:
            conn.close()

    @app.post("/proposals/<int:proposal_id>/decision")
    def proposals_decide(proposal_id):
        """Slice 4. The dispatcher is the seeded stand-in account; the caller
        cannot name who they are (real login replaces stub_dispatcher_id)."""
        body = request.get_json(silent=True) or {}
        conn = connect()
        try:
            result = decide_human(
                conn, proposal_id, body.get("decision"), stub_dispatcher_id(conn)
            )
        except DecideError as exc:
            status = {
                "PROPOSAL_NOT_FOUND": 404,
                "INVALID_DECISION": 400,
                "NOT_A_DISPATCHER": 403,
            }.get(exc.code, 500)
            return jsonify({"error": {"code": exc.code, "message": str(exc)}}), status
        except RegistryError as exc:
            return jsonify({"error": {"code": exc.code, "message": str(exc)}}), 409
        finally:
            conn.close()
        return jsonify(result)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
