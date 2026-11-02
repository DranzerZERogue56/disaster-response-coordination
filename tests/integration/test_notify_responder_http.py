import glob
import sqlite3

import pytest


def load_schema_and_seed(c):
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            c.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        c.executescript(f.read())


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "route.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    c = sqlite3.connect(db_path)
    load_schema_and_seed(c)
    c.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = True
    with app.test_client() as tc:
        yield tc


def post_report(client, text):
    return client.post(
        "/reports",
        json={
            "location": "4th & Main St",
            "severity_raw": text,
            "timestamp_reported": "2026-11-01T12:00:00+00:00",
            "reporting_unit": "field-unit-7",
        },
    )


def test_auto_approved_report_notifies_but_held_one_does_not_until_approved(client):
    a = post_report(client, "person fell, visible leg injury, conscious and talking").get_json()
    assert a["decision"]["final_status"] == "approved"
    assert a["notification"]["unit_id"] == a["reservation"]["unit_id"]
    assert a["notification"]["sent_at"]

    b = post_report(client, "something happened, not sure how bad, no one's answering").get_json()
    assert b["decision"]["held_for_human"] is True
    assert b["notification"] is None  # nothing final yet, nothing sent

    pid = b["proposal"]["proposal_id"]
    decided = client.post(f"/proposals/{pid}/decision", json={"decision": "approve"}).get_json()
    assert decided["notification"]["unit_id"] == b["reservation"]["unit_id"]

    again = client.post(f"/proposals/{pid}/decision", json={"decision": "approve"}).get_json()
    assert again["already_decided"] is True
    assert again["notification"] is None  # a repeat does not re-notify

