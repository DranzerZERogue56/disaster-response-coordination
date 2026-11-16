"""The two-factor sign-in over a real socket with a real cookie jar, the way a browser does it (not Flask's test client)."""
import glob
import http.cookiejar
import json
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest
from werkzeug.serving import make_server

from src.auth.service import enrol
from src.auth.totp import code_at, step_for


@pytest.fixture
def live(tmp_path, monkeypatch):
    db_path = tmp_path / "live_login.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("AUTH_ENFORCED", "1")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    for path in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    account = enrol(conn, "demo-dispatcher", "dispatcher")
    conn.close()
    from src.web_ui.app import create_app

    server = make_server("127.0.0.1", 0, create_app(), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", account
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def browser():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("Accept", "text/html")]  # what a browser sends; a script that does not is told 401 instead of redirected
    return opener, jar


def form(data):
    return urllib.parse.urlencode(data).encode("ascii")


def test_a_browser_can_sign_in_use_the_console_and_sign_out_over_a_real_socket(live):
    url, account = live
    opener, jar = browser()

    with pytest.raises(urllib.error.HTTPError) as refused:  # no session: a script is told 401
        opener.open(urllib.request.Request(url + "/proposals/pending", headers={"Accept": "application/json"}))
    assert refused.value.code == 401

    page = opener.open(url + "/dispatcher")  # a browser with no session is sent to the sign-in page
    assert page.geturl().endswith("/login") and "Sign in" in page.read().decode()

    code = code_at(account["totp_secret"], step_for(time.time()))
    signed_in = opener.open(url + "/login", data=form({"username": "demo-dispatcher", "password": account["password"], "code": code}))
    body = signed_in.read().decode()
    assert signed_in.geturl().endswith("/dispatcher") and "Dispatcher console" in body and "Sign out" in body
    cookie = next(c for c in jar if c.name == "session")
    assert cookie.has_nonstandard_attr("HttpOnly") and cookie.get_nonstandard_attr("SameSite") == "Strict"

    token = json.loads(opener.open(url + "/session").read())["csrf_token"]
    out = opener.open(url + "/logout", data=form({"csrf_token": token}))
    assert out.geturl().endswith("/login")
    again = opener.open(url + "/dispatcher")
    assert again.geturl().endswith("/login")  # signed out for real


def test_a_wrong_code_over_a_real_socket_is_a_401_with_no_cookie_that_works(live):
    url, account = live
    opener, _jar = browser()
    with pytest.raises(urllib.error.HTTPError) as refused:
        opener.open(url + "/login", data=form({"username": "demo-dispatcher", "password": account["password"], "code": "000000"}))
    assert refused.value.code == 401
    with pytest.raises(urllib.error.HTTPError):
        opener.open(urllib.request.Request(url + "/session", headers={"Accept": "application/json"}))
