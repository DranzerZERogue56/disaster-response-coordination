"""Dispatcher Web UI (docs/architecture.md §3/§5) — walking skeleton.

Serves the one real vertical slice this milestone requires: Submit
Incident Report -> Intake Gateway -> SQLite incident_reports -> a
rendered list a human can see. Every other interface in §5 (Classify &
Propose, Decide Proposal, etc.) is a stub — see docs/skeleton-trace.md
for what's real this week and what isn't.
"""
import os
import sqlite3
import sys
import threading
import time
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
from src.intake_gateway.queue import (
    drain_queue,
    is_connected,
    queued_report_ids,
    set_connected,
)
from src.intake_gateway.service import (
    InvalidBody,
    InvalidTimestamp,
    ValidationError,
    list_reports,
    submit_report,
)
from src.negotiation.service import contest
from src.notify_responder.service import (
    NotifyError,
    notify_for_decision,
    notify_responder,
)
from src.override_assignment.service import (
    OverrideError,
    add_follow_up,
    override_assignment,
)
from src.unit_registry.service import (
    RegistryError,
    release_expired,
    reserve_for_proposal,
    unit_clock,
)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def try_notify(conn, decision):
    """Notify after an approval. A failed notification never undoes the
    decision; it is reported next to it so a person can see it."""
    try:
        return notify_for_decision(conn, decision)
    except NotifyError as exc:
        return {"error": {"code": exc.code, "message": str(exc)}}


class UnitLostBeforeApproval(Exception):
    """The reserved unit vanished between reserving and auto-approving, and
    one automatic retry did not fix it. Carries the reservation so the
    response can still show it."""

    def __init__(self, reservation, cause):
        self.reservation = reservation
        self.cause = cause
        super().__init__(str(cause))


def reserve_and_decide(conn, proposal_id):
    """Reserve, then auto-decide immediately. If the unit was lost in the
    gap between the two, reserve again once and retry (see decide_auto's
    docstring for how a unit can be lost). Returns
    (reservation, decision, retried_after_loss)."""
    reservation = reserve_for_proposal(conn, proposal_id, on_conflict=contest)
    try:
        return reservation, decide_auto(conn, proposal_id), False
    except RegistryError as first:
        if first.code != "UNIT_NO_LONGER_AVAILABLE":
            raise
    reservation = reserve_for_proposal(conn, proposal_id, on_conflict=contest)
    try:
        return reservation, decide_auto(conn, proposal_id), True
    except RegistryError as second:
        raise UnitLostBeforeApproval(reservation, second) from second


def process_report(conn, result):
    """Everything that happens to a created report: classify, reserve, decide,
    notify. Fills `result` in place and returns the HTTP status (201, or 409
    when no unit could be reserved or the unit was lost)."""
    # Architecture 5: creating a report triggers Classify & Propose.
    # If it cannot classify, the report stays created for a human.
    try:
        result["proposal"] = classify_and_propose(conn, result["report_id"], get_model())
    except ClassifyError as exc:
        result["proposal"] = None
        result["needs_human"] = {"code": exc.code, "message": str(exc)}
    # Slice 2: reserve the proposed unit the moment it is proposed.
    # Its own call (not inside classify) so it can fail on its own.
    if result["proposal"]:
        try:
            (
                result["reservation"],
                result["decision"],
                retried,
            ) = reserve_and_decide(conn, result["proposal"]["proposal_id"])
            if retried:
                result["retried_after_unit_loss"] = True
            # Slice 5: tell the unit once the assignment is final.
            result["notification"] = try_notify(conn, result["decision"])
        except UnitLostBeforeApproval as exc:
            result["reservation"] = exc.reservation
            result["error"] = {
                "code": "UNIT_LOST_BEFORE_APPROVAL",
                "message": "The unit was reserved, then lost before the "
                "automatic approval could finish, twice. Nothing was "
                f"dispatched. Underlying: {exc.cause}",
                "underlying": exc.cause.code,
            }
            return 409
        except RegistryError as exc:
            result["reservation"] = None
            result["error"] = {
                "code": exc.code,
                "message": str(exc),
                "tried": exc.tried,
            }
            return 409
    return 201


def drain_one(conn, report_id):
    """Process one report released from the offline queue; returns a short
    summary so a reconnection response shows what happened to each."""
    result = {"report_id": report_id, "status": "created"}
    status = process_report(conn, result)
    summary = {"report_id": report_id, "http_status": status}
    if result.get("error"):
        summary["error"] = result["error"]["code"]
    elif result.get("decision"):
        summary["final_status"] = result["decision"].get("final_status")
        summary["held_for_human"] = bool(result["decision"].get("held_for_human"))
    elif result.get("needs_human"):
        summary["error"] = result["needs_human"]["code"]
    return summary


def start_sweeper(interval_seconds):
    """The set clock: every few seconds, free any reservation whose 4-minute
    window has run out, whether or not anyone is using the software."""

    def loop():
        while True:
            time.sleep(interval_seconds)
            try:
                conn = connect()
                try:
                    release_expired(conn)
                finally:
                    conn.close()
            except sqlite3.Error as exc:  # keep the clock alive; say what went wrong
                print(f"reservation sweeper error: {exc}", file=sys.stderr)

    threading.Thread(target=loop, daemon=True, name="reservation-sweeper").start()


def create_app():
    app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

    # script/start sets SWEEP_SECONDS; tests and imports leave it unset, so no
    # background thread starts unless the app is really being run.
    sweep = os.environ.get("SWEEP_SECONDS")
    if sweep:
        start_sweeper(float(sweep))

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
            units = unit_clock(conn)
        finally:
            conn.close()
        return render_template("reports.html", reports=reports, units=units)

    @app.get("/units")
    def units_clock():
        """Every unit, and for a reserved one when it will be freed."""
        conn = connect()
        try:
            return jsonify({"units": unit_clock(conn)})
        finally:
            conn.close()

    @app.post("/reports")
    def reports_create():
        conn = connect()
        try:
            run_id = ensure_scenario_run(conn)
            fields = request.get_json(silent=True) or request.form
            result = submit_report(conn, run_id, fields, queued=not is_connected())
            if result["status"] == "queued":
                # Slice 6: offline. The report is saved and waits in the queue.
                result["note"] = "offline: queued, will be processed on reconnection"
                return jsonify(result), 202
            status = process_report(conn, result)
            return jsonify(result), status
        except InvalidTimestamp as exc:
            return (
                jsonify({"error": {"code": "INVALID_TIMESTAMP", "message": str(exc)}}),
                400,
            )
        except InvalidBody as exc:
            return jsonify({"error": {"code": "INVALID_BODY", "message": str(exc)}}), 400
        except ValidationError as exc:
            return (
                jsonify(
                    {
                        "error": {
                            "code": exc.code,
                            "message": str(exc),
                            "field": exc.fields,
                        }
                    }
                ),
                400,
            )
        finally:
            conn.close()

    @app.get("/connectivity")
    def connectivity_status():
        conn = connect()
        try:
            waiting = len(queued_report_ids(conn))
        finally:
            conn.close()
        return jsonify({"connected": is_connected(), "queued_reports": waiting})

    @app.post("/connectivity")
    def connectivity_set():
        """Simulated network (the design's connectivity flag). Going back
        online drains the queue, oldest report first (FR-INTAKE-01)."""
        body = request.get_json(silent=True) or {}
        if not isinstance(body.get("connected"), bool):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_FLAG",
                            "message": 'send {"connected": true} or {"connected": false}',
                        }
                    }
                ),
                400,
            )
        set_connected(body["connected"])
        drained = []
        if body["connected"]:
            conn = connect()
            try:
                drained = drain_queue(conn, drain_one)
            finally:
                conn.close()
        return jsonify(
            {"connected": is_connected(), "drained_count": len(drained), "drained": drained}
        )

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
            dispatcher = stub_dispatcher_id(conn)
            try:
                result = decide_human(conn, proposal_id, body.get("decision"), dispatcher)
            except RegistryError as exc:
                if exc.code != "UNIT_NO_LONGER_AVAILABLE" or body.get("decision") != "approve":
                    raise
                # FR-RES-01-AC2: the held unit was lost before the dispatcher decided. Give the
                # incident a second path to a responder (the proposal's alternatives) and approve
                # that; only if no unit can be had does the dispatcher get the error.
                reserve_for_proposal(conn, proposal_id, on_conflict=contest)
                result = decide_human(conn, proposal_id, "approve", dispatcher)
                result["retried_after_unit_loss"] = True
            result["notification"] = try_notify(conn, result)
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

    @app.post("/assignments/<int:proposal_id>/override")
    def assignment_override(proposal_id):
        """Slice 7. Same stand-in dispatcher as slice 4; the caller cannot name one."""
        body = request.get_json(silent=True) or {}
        conn = connect()
        try:
            result = override_assignment(
                conn,
                proposal_id,
                body.get("new_unit_id"),
                body.get("reason"),
                stub_dispatcher_id(conn),
            )
            # Tell the unit that now holds the assignment.
            try:
                result["notification"] = notify_responder(
                    conn, proposal_id, result["new_unit_id"]
                )
            except NotifyError as exc:
                result["notification"] = {"error": {"code": exc.code, "message": str(exc)}}
        except OverrideError as exc:
            status = {
                "REASON_REQUIRED": 400,
                "ASSIGNMENT_NOT_FOUND": 404,
                "NOT_A_DISPATCHER": 403,
            }.get(exc.code, 400)
            return jsonify({"error": {"code": exc.code, "message": str(exc)}}), status
        except DecideError as exc:
            return jsonify({"error": {"code": exc.code, "message": str(exc)}}), 500
        except RegistryError as exc:
            return jsonify({"error": {"code": exc.code, "message": str(exc)}}), 409
        finally:
            conn.close()
        return jsonify(result)

    @app.post("/overrides/<int:override_id>/follow-up")
    def override_follow_up(override_id):
        body = request.get_json(silent=True) or {}
        conn = connect()
        try:
            result = add_follow_up(conn, override_id, body.get("text"), stub_dispatcher_id(conn))
        except OverrideError as exc:
            status = 404 if exc.code == "OVERRIDE_NOT_FOUND" else 400
            return jsonify({"error": {"code": exc.code, "message": str(exc)}}), status
        except DecideError as exc:
            return jsonify({"error": {"code": exc.code, "message": str(exc)}}), 500
        finally:
            conn.close()
        return jsonify(result)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
