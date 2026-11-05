"""Dispatcher console (docs/architecture.md section 5, Web UI), Milestone 11 / NFR-ACC-01, NFR-ACC-02.

One page, `GET /dispatcher`, for a person: the proposals waiting for a decision, the assignments in force, the
unit clock, node alerts and the incidents that need a person. Every action is a plain HTML form that POSTs and
redirects back with a message (post/redirect/get), so it works with the keyboard alone and without any
script. Nothing on the page reloads by itself, and a link or a prefetch can never trigger an action (the
action URLs accept POST only).

Severity is always a word plus a symbol, never colour alone (NFR-ACC-02). The dispatcher is the seeded
stand-in account, as for the JSON routes: real sign-in (FR-AUTH-01) is not built, so these forms carry no
login and no CSRF token; both arrive with sign-in.
"""
from flask import Blueprint, abort, redirect, render_template, request, url_for

from src.db import connect
from src.decide_proposal.service import DecideError, list_pending, stub_dispatcher_id
from src.heartbeat.service import HeartbeatError, confirm_recovery
from src.override_assignment.service import OverrideError
from src.unit_registry.service import RegistryError, unit_clock
from src.web_ui.actions import decide_with_retry, override_with_notice

bp = Blueprint("dispatcher", __name__)

# The five NFPA levels, each with its own symbol (a shape, so the levels differ without colour).
LEVELS = (
    ("Minor", "○"),  # circle
    ("Moderate", "◇"),  # diamond
    ("Serious", "△"),  # triangle
    ("Severe", "▲"),  # filled triangle
    ("Critical", "■"),  # filled square
)
SYMBOLS = dict(LEVELS)
MAX_NOTICE = 300
HINTS = {
    "UNIT_ALREADY_RESERVED": "Choose a different unit.",
    "UNIT_UNAVAILABLE": "Choose a different unit.",
    "UNIT_NOT_FOUND": "Check the unit number in the Units table.",
    "MODIFIED_UNIT_REQUIRED": "Type the number of the unit to send instead.",
    "MODIFIED_UNIT_UNCHANGED": "That is the unit already proposed; use Approve instead.",
    "REASON_REQUIRED": "Type a reason, then try again.",
    "NODE_NOT_RESUMED": "Wait until the node responds again.",
}
ERRORS = (DecideError, RegistryError, OverrideError, HeartbeatError, LookupError)


def _severity(level):
    if level in SYMBOLS:
        return {"slug": level.lower(), "symbol": SYMBOLS[level], "severity_label": level}
    return {"slug": "unclassified", "symbol": "?", "severity_label": "Not yet classified"}


def _whole_number(text):
    text = (text or "").strip()
    return int(text) if text.isdigit() else None


def _refused(what, exc):
    code = getattr(exc, "code", "NOT_FOUND")
    return _back(f"{what} was not changed: {exc} ({code}). {HINTS.get(code, '')}".strip(), False)


def _back(message, ok):
    return redirect(url_for("dispatcher.console", notice=message[:MAX_NOTICE], ok="1" if ok else "0"), code=303)


@bp.get("/dispatcher")
def console():
    conn = connect()
    try:
        units = unit_clock(conn)  # first: it frees expired holds, which also settles their proposals
        seconds_left = {u["unit_id"]: u["seconds_left"] for u in units}
        pending = [
            {**p, **_severity(p["severity"]), "seconds_left": seconds_left.get(p["recommended_unit_id"])}
            for p in list_pending(conn)
        ]
        assignments = [
            {**dict(r), **_severity(r["severity"])}
            for r in conn.execute(
                "SELECT p.id AS proposal_id, p.final_status, r.id AS report_id, r.location, r.severity, u.id AS unit_id "
                "FROM units u JOIN agent_proposals p ON p.id = u.reserved_by_proposal_id "
                "JOIN incident_reports r ON r.id = p.report_id WHERE u.status = 'assigned' ORDER BY p.id"
            )
        ]
        alerts = [dict(r) for r in conn.execute("SELECT * FROM node_alerts WHERE confirmed_at IS NULL ORDER BY id")]
        escalations = [
            dict(r) for r in conn.execute("SELECT report_id, reason, created_at FROM human_escalations WHERE resolved_at IS NULL ORDER BY id")
        ]
    finally:
        conn.close()
    return render_template(
        "dispatcher.html",
        pending=pending,
        assignments=assignments,
        units=units,
        alerts=alerts,
        escalations=escalations,
        levels=[{"label": label, "symbol": symbol} for label, symbol in LEVELS],
        notice=request.args.get("notice", "")[:MAX_NOTICE],
        ok=request.args.get("ok") == "1",
    )


@bp.post("/dispatcher/proposals/<int:proposal_id>/<action>")
def decide(proposal_id, action):
    decision = {"approve": "approve", "modify": "modify", "reject": "reject"}.get(action)
    if decision is None:
        abort(404)
    conn = connect()
    try:
        result = decide_with_retry(
            conn,
            proposal_id,
            decision,
            stub_dispatcher_id(conn),
            modified_unit_id=_whole_number(request.form.get("modified_unit_id")) if decision == "modify" else None,
        )
    except ERRORS as exc:
        return _refused(f"Proposal {proposal_id}", exc)
    finally:
        conn.close()
    if result.get("already_decided"):
        return _back(f"Proposal {proposal_id} was already {result['final_status']}; nothing changed.", True)
    if decision == "approve":
        unit = (result.get("notification") or {}).get("unit_id")
        return _back(f"Proposal {proposal_id} approved" + (f"; unit {unit} notified." if unit else "."), True)
    if decision == "modify":
        return _back(f"Proposal {proposal_id} modified: unit {result['unit_id']} assigned instead.", True)
    return _back(f"Proposal {proposal_id} rejected; its unit was freed.", True)


@bp.post("/dispatcher/assignments/<int:proposal_id>/override")
def override(proposal_id):
    conn = connect()
    try:
        result = override_with_notice(
            conn,
            proposal_id,
            _whole_number(request.form.get("new_unit_id")),
            request.form.get("reason"),
            stub_dispatcher_id(conn),
        )
    except ERRORS as exc:
        return _refused(f"Assignment for proposal {proposal_id}", exc)
    finally:
        conn.close()
    return _back(f"Assignment for proposal {proposal_id} moved to unit {result['new_unit_id']}.", True)


@bp.post("/dispatcher/nodes/<int:node_id>/confirm-recovery")
def confirm_node(node_id):
    conn = connect()
    try:
        confirm_recovery(conn, node_id, stub_dispatcher_id(conn))
    except ERRORS as exc:
        return _refused(f"Node {node_id}", exc)
    finally:
        conn.close()
    return _back(f"Node {node_id} confirmed recovered.", True)
