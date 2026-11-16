"""Two-factor sign-in through the real routes with AUTH_ENFORCED=1 (plan Task 4, the five Review Focus lines)."""
import glob
import sqlite3
import time
from pathlib import Path

import pytest

from src.auth.service import enrol
from src.auth.totp import code_at, step_for
from tests.html_helpers import form_with_button, parse

GATED = [
    ("get", "/dispatcher"),
    ("get", "/reports"),
    ("get", "/units"),
    ("get", "/alerts"),
    ("get", "/proposals/pending"),
    ("get", "/connectivity"),
    ("get", "/session"),
    ("post", "/reports"),
    ("post", "/connectivity"),
    ("post", "/proposals/1/decision"),
    ("post", "/assignments/1/override"),
    ("post", "/overrides/1/follow-up"),
    ("post", "/reconciliations/1/override"),
    ("post", "/nodes/1/heartbeat"),
    ("post", "/nodes/1/confirm-recovery"),
    ("post", "/dispatcher/proposals/1/approve"),
    ("post", "/logout"),
]


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "login.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("AUTH_ENFORCED", "1")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    accounts = {
        "demo-dispatcher": enrol(conn, "demo-dispatcher", "dispatcher"),
        "watcher": enrol(conn, "watcher", "observer"),
    }
    conn.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    yield app, accounts, db_path


def now_code(account, offset_steps=0):
    return code_at(account["totp_secret"], step_for(time.time()) + offset_steps)


def sign_in_as(client, account, code=None):
    return client.post(
        "/login",
        data={"username": account["username"], "password": account["password"], "code": code or now_code(account)},
    )


@pytest.mark.covers("FR-AUTH-01-AC2")
@pytest.mark.parametrize(("method", "path"), GATED)
def test_every_route_except_health_and_login_refuses_a_caller_with_no_session_and_changes_nothing(world, method, path):
    app, _accounts, db = world
    before = sqlite3.connect(db).execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0]
    with app.test_client() as client:
        response = getattr(client, method)(path, json={"location": "x"} if method == "post" else None)
    assert response.status_code in (401, 303), f"{method} {path} answered {response.status_code}"
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM incident_reports").fetchone()[0] == before


def test_health_and_the_login_page_stay_open_and_a_page_request_is_sent_to_the_login(world):
    app, _a, _d = world
    with app.test_client() as client:
        assert client.get("/healthz").status_code == 200 and client.get("/login").status_code == 200
        redirect = client.get("/dispatcher", headers={"Accept": "text/html"})
        assert redirect.status_code == 303 and redirect.headers["Location"].endswith("/login")


@pytest.mark.covers("FR-AUTH-01-AC1")
def test_signing_in_with_the_right_password_and_the_right_code_opens_the_console(world):
    app, accounts, _d = world
    with app.test_client() as client:
        response = sign_in_as(client, accounts["demo-dispatcher"])
        assert response.status_code == 303 and response.headers["Location"].endswith("/dispatcher")
        assert client.get("/dispatcher").status_code == 200


@pytest.mark.covers("FR-AUTH-01-AC1")
@pytest.mark.parametrize("which", ["wrong_code", "wrong_password", "no_code", "unknown_user"])
def test_a_failed_sign_in_gives_one_message_and_no_session(world, which):
    app, accounts, _d = world
    account = accounts["demo-dispatcher"]
    data = {"username": "demo-dispatcher", "password": account["password"], "code": now_code(account)}
    if which == "wrong_code":
        data["code"] = "000000"
    elif which == "wrong_password":
        data["password"] = "not it"
    elif which == "no_code":
        data["code"] = ""
    else:
        data["username"] = "nobody"
    with app.test_client() as client:
        response = client.post("/login", data=data)
        assert response.status_code == 401 and "Sign-in failed" in response.get_data(as_text=True)
        assert client.get("/dispatcher", headers={"Accept": "text/html"}).status_code == 303


def test_the_login_page_is_a_labelled_form(world):
    app, _a, _d = world
    root = parse(app.test_client().get("/login").get_data(as_text=True))
    labels = {n.attrs["for"] for n in root.find_all("label") if "for" in n.attrs}
    inputs = [n for n in root.find_all("input") if n.attrs.get("type") != "hidden"]
    assert len(inputs) == 3 and all(i.attrs.get("id") in labels for i in inputs)
    assert root.find_all("html")[0].attrs.get("lang") == "en" and len(root.find_all("h1")) == 1


@pytest.mark.covers("FR-AUTH-01-AC2")
def test_a_post_with_a_valid_session_but_no_forgery_token_is_refused(world):
    app, accounts, _d = world
    with app.test_client() as client:
        sign_in_as(client, accounts["demo-dispatcher"])
        refused = client.post("/dispatcher/proposals/1/approve")
        assert refused.status_code == 403 and refused.get_json()["error"]["code"] == "CSRF_TOKEN_REQUIRED"
        wrong = client.post("/proposals/1/decision", json={"decision": "approve"}, headers={"X-CSRF-Token": "guess"})
        assert wrong.status_code == 403


def test_the_token_from_the_session_lets_a_script_through_to_the_real_route(world):
    app, accounts, _d = world
    with app.test_client() as client:
        sign_in_as(client, accounts["demo-dispatcher"])
        token = client.get("/session").get_json()["csrf_token"]
        response = client.post("/proposals/999/decision", json={"decision": "approve"}, headers={"X-CSRF-Token": token})
        assert response.status_code == 404  # past the gate, and the route says there is no such proposal


def test_the_console_forms_carry_the_token_and_pressing_a_button_works(world):
    app, accounts, db = world
    with app.test_client() as client:
        sign_in_as(client, accounts["demo-dispatcher"])
        body = {"location": "4th & Main St", "severity_raw": "something happened, not sure how bad, no one is answering", "timestamp_reported": "2026-11-01T12:00:00+00:00", "reporting_unit": "u"}
        token = client.get("/session").get_json()["csrf_token"]
        created = client.post("/reports", json=body, headers={"X-CSRF-Token": token}).get_json()
        pid = created["proposal"]["proposal_id"]
        form = form_with_button(parse(client.get("/dispatcher").get_data(as_text=True)), f"Approve proposal {pid}")
        assert form["fields"]["csrf_token"] == token
        response = client.post(form["action"], data=form["fields"], follow_redirects=True)
        assert response.status_code == 200
    assert sqlite3.connect(db).execute("SELECT final_status FROM agent_proposals WHERE id = ?", (pid,)).fetchone()[0] == "approved"


@pytest.mark.covers("FR-AUTH-01-AC2")
def test_logging_out_ends_the_session_even_for_a_copied_cookie(world):
    app, accounts, _d = world
    with app.test_client() as first:
        sign_in_as(first, accounts["demo-dispatcher"])
        copied = first.get_cookie("session").value
        token = first.get("/session").get_json()["csrf_token"]
        assert first.post("/logout", data={"csrf_token": token}).status_code == 303
        assert first.get("/dispatcher", headers={"Accept": "text/html"}).status_code == 303
    with app.test_client() as thief:
        thief.set_cookie("session", copied)
        assert thief.get("/dispatcher", headers={"Accept": "text/html"}).status_code == 303
        assert thief.get("/session").status_code == 401


def test_a_cookie_made_before_a_restart_is_refused_by_the_new_process(world, monkeypatch):
    app, accounts, _d = world
    with app.test_client() as client:
        sign_in_as(client, accounts["demo-dispatcher"])
        cookie = client.get_cookie("session").value
    from src.web_ui.app import create_app

    with create_app().test_client() as restarted:
        restarted.set_cookie("session", cookie)
        assert restarted.get("/session").status_code == 401


@pytest.mark.covers("FR-AUTH-01-AC2")
def test_an_observer_can_sign_in_but_every_action_is_refused(world):
    app, accounts, db = world
    with app.test_client() as client:
        assert sign_in_as(client, accounts["watcher"]).status_code == 303
        token = client.get("/session").get_json()["csrf_token"]
        assert client.get("/dispatcher").status_code == 200  # may look
        decision = client.post("/proposals/1/decision", json={"decision": "approve"}, headers={"X-CSRF-Token": token})
        assert decision.status_code == 403 and decision.get_json()["error"]["code"] == "NOT_A_DISPATCHER"
        override = client.post("/assignments/1/override", json={"new_unit_id": 2, "reason": "x"}, headers={"X-CSRF-Token": token})
        assert override.status_code == 403


def test_the_session_cookie_is_http_only_and_same_site_strict(world):
    app, accounts, _d = world
    with app.test_client() as client:
        header = sign_in_as(client, accounts["demo-dispatcher"]).headers.get("Set-Cookie", "")
    assert "HttpOnly" in header and "SameSite=Strict" in header


def test_with_the_gate_off_nothing_changes(world, monkeypatch):
    app, _a, _d = world
    monkeypatch.delenv("AUTH_ENFORCED")
    with app.test_client() as client:
        assert client.get("/dispatcher").status_code == 200 and client.get("/reports").status_code == 200
