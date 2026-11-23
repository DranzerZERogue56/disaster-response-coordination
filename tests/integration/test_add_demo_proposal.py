"""tools/add_demo_proposal.py: one vague report that the rules model is unsure about, so a person must decide."""
import glob
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import add_demo_proposal


def make_db(path):
    conn = sqlite3.connect(path)
    for migration in sorted(glob.glob("migrations/*.sql")):
        conn.executescript(Path(migration).read_text(encoding="utf-8"))
    conn.executescript(Path("seed/iteration-1.sql").read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def test_it_leaves_one_proposal_waiting_for_a_person_and_a_unit_held_for_it(tmp_path, monkeypatch):
    db = tmp_path / "demo.sqlite"
    make_db(db)
    monkeypatch.delenv("AUTH_ENFORCED", raising=False)
    result = add_demo_proposal.add(str(db))
    conn = sqlite3.connect(db)
    waiting = conn.execute("SELECT id FROM agent_proposals WHERE final_status IS NULL").fetchall()
    held = conn.execute("SELECT status FROM units WHERE id = ?", (result["unit_id"],)).fetchone()[0]
    assert [row[0] for row in waiting] == [result["proposal_id"]]
    assert held == "reserved"


def test_it_leaves_the_callers_environment_as_it_found_it(tmp_path, monkeypatch):
    import os

    db = tmp_path / "demo.sqlite"
    make_db(db)
    monkeypatch.delenv("AUTH_ENFORCED", raising=False)
    monkeypatch.delenv("DB_PATH", raising=False)
    add_demo_proposal.add(str(db))
    assert "AUTH_ENFORCED" not in os.environ and "DB_PATH" not in os.environ


def test_it_works_twice_in_a_row_and_never_touches_an_unreachable_database(tmp_path, monkeypatch):
    db = tmp_path / "demo.sqlite"
    make_db(db)
    monkeypatch.delenv("AUTH_ENFORCED", raising=False)
    first, second = add_demo_proposal.add(str(db)), add_demo_proposal.add(str(db))
    assert first["proposal_id"] != second["proposal_id"]
    try:
        add_demo_proposal.add(str(tmp_path / "missing" / "nope.sqlite"))
    except SystemExit as exc:
        assert "database" in str(exc.code)
    else:
        raise AssertionError("a missing database must stop with a clear message")
