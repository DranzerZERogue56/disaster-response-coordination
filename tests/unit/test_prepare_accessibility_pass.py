"""The prep tool for the manual keyboard-only pass (NFR-ACC-01) leaves a known, stable starting state."""
import sqlite3
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import prepare_accessibility_pass as prep


def rows(db, sql):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql)]
    conn.close()
    return out


def test_it_leaves_three_pending_proposals_one_assignment_and_free_units_for_modify_and_override(tmp_path, monkeypatch):
    db = tmp_path / "acc01.sqlite"
    summary = prep.prepare(str(db))

    pending = rows(db, "SELECT id FROM agent_proposals WHERE final_status IS NULL")
    assigned = rows(db, "SELECT id, reserved_by_proposal_id FROM units WHERE status = 'assigned'")
    free = rows(db, "SELECT id FROM units WHERE status = 'available'")
    assert len(pending) == 3 and len(assigned) == 1 and len(free) >= 3
    assert summary["pending_proposals"] == [p["id"] for p in pending] and summary["assigned_proposal"] == assigned[0]["reserved_by_proposal_id"]
    assert rows(db, "SELECT COUNT(*) AS n FROM units WHERE status = 'reserved'")[0]["n"] == 0  # no hold is left to run out mid-pass


def test_the_pending_proposals_do_not_expire_while_a_person_works_through_them(tmp_path):
    db = tmp_path / "acc01.sqlite"
    prep.prepare(str(db))
    from datetime import UTC, datetime, timedelta

    from src.unit_registry.service import release_expired

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    release_expired(conn, now=datetime.now(UTC) + timedelta(hours=1))  # an hour later: the sweeper has run many times
    assert conn.execute("SELECT COUNT(*) FROM agent_proposals WHERE final_status IS NULL").fetchone()[0] == 3
    conn.close()


def test_preparing_twice_starts_from_scratch_each_time(tmp_path):
    db = tmp_path / "acc01.sqlite"
    prep.prepare(str(db))
    time.sleep(0.01)
    again = prep.prepare(str(db))
    assert len(rows(db, "SELECT id FROM incident_reports")) == 4 and len(again["pending_proposals"]) == 3


def test_all_four_actions_of_the_manual_script_succeed_on_the_prepared_state(tmp_path, monkeypatch):
    """So that a failure during the manual pass is a real finding, not a problem with the preparation."""
    from tests.html_helpers import form_with_button, parse

    db = tmp_path / "acc01.sqlite"
    summary = prep.prepare(str(db))
    monkeypatch.setenv("DB_PATH", str(db))
    from src.web_ui.app import create_app

    approve, modify, reject = summary["pending_proposals"]
    override = summary["assigned_proposal"]
    with create_app().test_client() as client:

        def press(button, **values):
            form = form_with_button(parse(client.get("/dispatcher").get_data(as_text=True)), button)
            return client.post(form["action"], data={**form["fields"], **{k: str(v) for k, v in values.items()}}, follow_redirects=True)

        spare = [r["id"] for r in rows(db, "SELECT id FROM units WHERE status = 'available' ORDER BY id")]
        press(f"Approve proposal {approve}")
        press(f"Modify proposal {modify}", modified_unit_id=spare[-1])
        press(f"Reject proposal {reject}")
        press(f"Override assignment {override}", new_unit_id=spare[-2], reason="manual pass check")

    status = {r["id"]: r["final_status"] for r in rows(db, "SELECT id, final_status FROM agent_proposals")}
    assert (status[approve], status[modify], status[reject]) == ("approved", "modified", "rejected")
    assert rows(db, "SELECT COUNT(*) AS n FROM dispatcher_overrides")[0]["n"] == 1
