"""Seam S4 with nothing in between: the scenario command-line tool talks over a real socket to a real running server.

Every other scenario test uses Flask's in-process test client. Here a genuine HTTP server (werkzeug, on 127.0.0.1 and
an ephemeral port) serves the app in a thread, and `tools/play_scenario.py` posts the demo scenario to it with
urllib, exactly as an operator would. The server is stopped in `finally`.
"""
import glob
import sqlite3
import sys
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from play_scenario import main as play_cli

SCENARIO = Path("seed/scenarios/demo-scenario.json")


@pytest.fixture
def live(tmp_path, monkeypatch):
    db_path = tmp_path / "live.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    conn.close()
    from src.web_ui.app import create_app

    server = make_server("127.0.0.1", 0, create_app(), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", db_path
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_the_command_line_plays_the_demo_scenario_into_a_real_running_server(live, capsys):
    url, db = live

    code = play_cli([str(SCENARIO), "--speed", "1000", "--url", url])

    out = capsys.readouterr().out
    assert code == 0 and out.count("HTTP 201") == 3
    check = sqlite3.connect(db)
    places = [r[0] for r in check.execute("SELECT location FROM incident_reports ORDER BY id")]
    logged = [r[0] for r in check.execute("SELECT reason FROM tiebreak_log")]
    check.close()
    assert places == ["4th & Main St", "Oak Street shelter", "9th & Pine"]  # all three arrived, in order, over a real socket
    assert logged == ["severity"]  # and the negotiation ran on the server side
