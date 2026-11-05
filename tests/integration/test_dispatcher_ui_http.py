"""Task 12: the dispatcher console, driven the way a person drives it: by reading the page and posting its forms."""
import glob
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from src.heartbeat.service import check_nodes, heartbeat
from tests.html_helpers import form_with_button, parse

VAGUE = "something happened, not sure how bad, no one is answering"  # confidence 40: held for a dispatcher
PAST = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)  # before the app's real clock, so a real heartbeat counts


@pytest.fixture
def world(tmp_path, monkeypatch):
    db_path = tmp_path / "dispatcher_ui.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    for _ in range(4):  # spare units, so modify and override have somewhere to go
        conn.execute("INSERT INTO units (scenario_run_id, unit_type, agent_node_id, status) VALUES (1, 'Medical', 1, 'available')")
    conn.commit()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client, conn


def report(client, place):
    body = {
        "location": place,
        "severity_raw": VAGUE,
        "timestamp_reported": "2026-11-01T12:00:00+00:00",
        "reporting_unit": "field-unit-7",
    }
    return client.post("/reports", json=body).get_json()


def page(client, follow=None):
    response = client.get("/dispatcher")
    assert response.status_code == 200
    return parse(response.get_data(as_text=True))


def submit(client, form, **values):
    data = {**form["fields"], **{k: str(v) for k, v in values.items()}}
    return client.post(form["action"], data=data, follow_redirects=True)


def notice_text(response):
    root = parse(response.get_data(as_text=True))
    return " ".join(n.text() for n in root.find_all("div") if "notice" in n.classes)


def test_the_console_shows_the_queue_the_units_the_alerts_and_the_escalations_on_one_page(world):
    client, conn = world
    report(client, "4th & Main St")
    conn.execute("INSERT INTO human_escalations (report_id, proposal_id, reason, created_at) VALUES (1, NULL, 'MODEL_CHAIN_EXHAUSTED', 't')")
    conn.execute("UPDATE agent_nodes SET last_heartbeat_at = ?", (PAST.isoformat(),))
    conn.commit()
    check_nodes(conn, now=PAST + timedelta(seconds=45))

    root = page(client)
    text = root.text()

    assert "4th & Main St" in text and "Proposals waiting for a decision" in text
    assert "Node 1" in text and "has not responded" in text  # the node alert
    assert "MODEL_CHAIN_EXHAUSTED" in text  # the escalation
    assert len(root.find_all("tr")) >= 6  # the units table: a header and the six units
    assert root.find_all("meta", http_equiv="refresh") == []  # nothing reloads under a person's hands (WCAG 2.2.1)


def test_all_four_actions_work_through_the_page_forms(world):
    client, conn = world
    ids = [report(client, f"{n} Elm St")["proposal"]["proposal_id"] for n in range(1, 5)]
    approve_id, modify_id, reject_id, override_id = ids

    root = page(client)
    assert submit(client, form_with_button(root, f"Approve proposal {approve_id}")).status_code == 200
    spare = conn.execute("SELECT id FROM units WHERE status = 'available' ORDER BY id").fetchall()
    submit(client, form_with_button(root, f"Modify proposal {modify_id}"), modified_unit_id=spare[0]["id"])
    submit(client, form_with_button(root, f"Reject proposal {reject_id}"))
    submit(client, form_with_button(root, f"Approve proposal {override_id}"))

    status = {r["id"]: r["final_status"] for r in conn.execute("SELECT id, final_status FROM agent_proposals")}
    assert status == {approve_id: "approved", modify_id: "modified", reject_id: "rejected", override_id: "approved"}

    root = page(client)  # the approved ones now appear under assignments, each with an override form
    override = form_with_button(root, f"Override assignment {override_id}")
    response = submit(client, override, new_unit_id=spare[1]["id"], reason="closer to the scene")
    assert "closer to the scene" not in notice_text(response)  # the notice confirms, it does not echo free text back
    assert conn.execute("SELECT COUNT(*) FROM dispatcher_overrides").fetchone()[0] == 1
    assert conn.execute("SELECT reason FROM dispatcher_overrides").fetchone()[0] == "closer to the scene"
    assert conn.execute("SELECT status FROM units WHERE id = ?", (spare[1]["id"],)).fetchone()[0] == "assigned"


def test_a_refused_action_is_explained_in_words_on_the_page_and_changes_nothing(world):
    client, conn = world
    first = report(client, "1 Elm St")["proposal"]["proposal_id"]
    second = report(client, "2 Elm St")
    taken = second["reservation"]["unit_id"]

    response = submit(client, form_with_button(page(client), f"Modify proposal {first}"), modified_unit_id=taken)

    assert response.status_code == 200
    message = notice_text(response)
    assert "Unit 2 is reserved" in message and "UNIT_ALREADY_RESERVED" in message and "Choose a different unit" in message
    assert conn.execute("SELECT final_status FROM agent_proposals WHERE id = ?", (first,)).fetchone()[0] is None

    blank = submit(client, form_with_button(page(client), f"Modify proposal {first}"), modified_unit_id="")
    assert "MODIFIED_UNIT_REQUIRED" in notice_text(blank)


def test_an_override_without_a_reason_is_refused_in_words(world):
    client, conn = world
    pid = report(client, "1 Elm St")["proposal"]["proposal_id"]
    submit(client, form_with_button(page(client), f"Approve proposal {pid}"))
    form = form_with_button(page(client), f"Override assignment {pid}")
    response = submit(client, form, new_unit_id=3, reason="  ")
    assert "REASON_REQUIRED" in notice_text(response) and conn.execute("SELECT COUNT(*) FROM dispatcher_overrides").fetchone()[0] == 0


def test_a_flagged_node_is_confirmed_recovered_from_the_page(world):
    client, conn = world
    conn.execute("UPDATE agent_nodes SET last_heartbeat_at = ?", (PAST.isoformat(),))
    conn.commit()
    check_nodes(conn, now=PAST + timedelta(seconds=45))
    assert "waiting for the node" in page(client).text()  # not resumed yet: no button to press
    assert not [b for b in page(client).find_all("button") if b.text().startswith("Confirm node 1")]

    heartbeat(conn, 1)  # the node answers again, on the real clock
    response = submit(client, form_with_button(page(client), "Confirm node 1 has recovered and its information is intact"))

    assert "recovered" in notice_text(response)
    assert conn.execute("SELECT status FROM agent_nodes WHERE id = 1").fetchone()[0] == "recovered"


def test_the_action_urls_only_accept_posts_so_a_link_or_a_prefetch_cannot_trigger_them(world):
    client, _conn = world
    pid = report(client, "1 Elm St")["proposal"]["proposal_id"]
    for action in ("approve", "reject", "modify"):
        assert client.get(f"/dispatcher/proposals/{pid}/{action}").status_code == 405
    assert client.get(f"/dispatcher/assignments/{pid}/override").status_code == 405
    assert client.get("/dispatcher/nodes/1/confirm-recovery").status_code == 405
    assert client.post(f"/dispatcher/proposals/{pid}/explode").status_code == 404


def test_an_empty_system_renders_without_error(world):
    client, _conn = world
    assert "No proposals are waiting" in page(client).text()


def test_a_notice_in_the_address_is_shown_as_text_never_as_markup(world):
    client, _conn = world
    response = client.get("/dispatcher?notice=%3Cscript%3Ealert(1)%3C/script%3E&ok=0")
    body = response.get_data(as_text=True)
    assert "<script>alert(1)</script>" not in body and "&lt;script&gt;" in body


def test_an_unknown_action_is_a_plain_404_not_a_redirect(world):
    client, _conn = world
    response = client.post("/dispatcher/proposals/1/explode")
    assert response.status_code == 404 and "Location" not in response.headers


@pytest.mark.parametrize("path", ["/proposals/1/decision", "/assignments/1/override", "/overrides/1/follow-up", "/connectivity"])
@pytest.mark.parametrize("body", [[1, 2], 5, "text", None])
def test_json_routes_survive_a_body_that_is_not_an_object(world, path, body):
    """Review finding: a JSON list used to crash four routes with a 500."""
    client, _conn = world
    assert client.post(path, json=body).status_code < 500
