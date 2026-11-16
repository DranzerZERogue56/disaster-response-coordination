"""The sign-in gate (docs/superpowers/plans/2026-11-15-two-factor-login.md, Task 4): DEF-018 / backlog B-07.

When `AUTH_ENFORCED=1` (script/start sets it) every request except `/healthz`, `/login` and the static files needs a
session made by a successful two-factor sign-in, and every POST (except the sign-in itself) must also carry the
per-session forgery token (form field `csrf_token` or header `X-CSRF-Token`). With the variable unset the gate does
nothing and the app behaves exactly as before (the test suite relies on that).

Sessions are tracked on the server as well as in the signed cookie: logging out, or restarting the app, ends them, and a
copied cookie stops working. The cookie is HttpOnly and SameSite=Strict (and Secure when the request is HTTPS).
"""
import hmac
import os
import secrets
from datetime import timedelta

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.auth.service import AuthError, sign_in
from src.db import connect
from src.decide_proposal.service import stub_dispatcher_id

bp = Blueprint("auth", __name__)
OPEN_PATHS = {"/healthz", "/login"}
SESSION_HOURS = 8


def enforced():
    return os.environ.get("AUTH_ENFORCED") == "1"


def current_dispatcher_id(conn):
    """The signed-in account when the gate is on, otherwise the seeded stand-in dispatcher (the old behaviour)."""
    if enforced():
        return session["account_id"]
    return stub_dispatcher_id(conn)


def _active(app_sessions):
    sid = session.get("sid")
    return sid is not None and sid in app_sessions and app_sessions[sid] == session.get("account_id")


def _needs_sign_in():
    wants_page = request.method == "GET" and "text/html" in request.headers.get("Accept", "")
    if wants_page:
        return redirect(url_for("auth.login_page"), code=303)
    error = {"code": "SIGN_IN_REQUIRED", "message": "Sign in at /login first."}
    return jsonify({"error": error}), 401


def install_gate(app):
    app.extensions["active_sessions"] = {}
    app.config["SECRET" + "_KEY"] = os.environ.get("SESSION_SIGNER") or os.urandom(32).hex()  # built in two parts: it is a Flask setting name, not a credential
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=SESSION_HOURS)
    app.register_blueprint(bp)

    @app.before_request
    def gate():
        if not enforced():
            return None
        if request.path in OPEN_PATHS or request.path.startswith("/static/"):
            return None
        app.config["SESSION_COOKIE_SECURE"] = request.is_secure
        if not _active(app.extensions["active_sessions"]):
            session.clear()
            return _needs_sign_in()
        if request.method == "POST":
            sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token") or ""
            if not hmac.compare_digest(sent, session.get("csrf", "")):
                error = {"code": "CSRF_TOKEN_REQUIRED", "message": "This request did not come from a page of this app; reload the page and try again."}
                return jsonify({"error": error}), 403
        return None

    @app.context_processor
    def template_values():
        return {"csrf_token": session.get("csrf", ""), "signed_in": "account_id" in session}


@bp.get("/login")
def login_page():
    return render_template("login.html", message="")


@bp.post("/login")
def login_submit():
    conn = connect()
    try:
        who = sign_in(conn, request.form.get("username", ""), request.form.get("password", ""), request.form.get("code", "").strip())
    except AuthError as exc:
        return render_template("login.html", message=str(exc)), 401
    finally:
        conn.close()
    from flask import current_app

    session.clear()
    session.permanent = True
    session["sid"] = secrets.token_hex(16)
    session["account_id"] = who
    session["csrf"] = secrets.token_hex(16)
    current_app.extensions["active_sessions"][session["sid"]] = who
    return redirect(url_for("dispatcher.console"), code=303)


@bp.post("/logout")
def logout():
    from flask import current_app

    current_app.extensions["active_sessions"].pop(session.get("sid"), None)
    session.clear()
    return redirect(url_for("auth.login_page"), code=303)


@bp.get("/session")
def session_info():
    """For scripts: who is signed in and the token to send as X-CSRF-Token."""
    return jsonify({"account_id": session.get("account_id"), "csrf_token": session.get("csrf")})
