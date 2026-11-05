"""Task 12: the dispatcher console is usable by keyboard and does not rely on colour (NFR-ACC-01 support, NFR-ACC-02)."""
import glob
import itertools
import re
import sqlite3
from pathlib import Path

import pytest

from tests.html_helpers import parse

CSS = Path("src/web_ui/static/dispatcher.css")
LEVELS = ("Minor", "Moderate", "Serious", "Severe", "Critical")


@pytest.fixture
def console(tmp_path, monkeypatch):
    """The rendered page with five pending incidents, one per NFPA level, and one assigned incident."""
    db_path = tmp_path / "accessibility.sqlite"
    monkeypatch.setenv("DB_PATH", str(db_path))
    conn = sqlite3.connect(db_path)
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path, encoding="utf-8") as f:
            conn.executescript(f.read())
    with open("seed/iteration-1.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    for place, level in zip(("Alpha St", "Bravo St", "Charlie St", "Delta St", "Echo St"), LEVELS, strict=True):
        rid = conn.execute(
            "INSERT INTO incident_reports (scenario_run_id, location, severity_raw, timestamp_reported, reporting_unit, status, received_at, severity) "
            "VALUES (1, ?, 'synthetic text', 't', 'u', 'classified', 't', ?)",
            (place, level),
        ).lastrowid
        conn.execute(
            "INSERT INTO agent_proposals (report_id, agent_node_id, confidence, recommended_unit_id, reasoning, alternatives, "
            "model_identifier, model_version, generated_at) VALUES (?, 1, 60, 1, 'because', '[]', 'fake', '1', 't')",
            (rid,),
        )
    conn.commit()
    conn.close()
    from src.web_ui.app import create_app

    app = create_app()
    app.testing = False
    with app.test_client() as client:
        yield client.get("/dispatcher").get_data(as_text=True)


def spoken_text(node):
    """The words a person (or a screen reader) gets from a node: everything except aria-hidden decoration."""
    if node.attrs.get("aria-hidden") == "true":
        return ""
    parts = [c if isinstance(c, str) else spoken_text(c) for c in node.children]
    return " ".join("".join(parts).split())


def luminance(hex_color):
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def variables():
    block = re.search(r":root\s*{([^}]*)}", CSS.read_text(encoding="utf-8")).group(1)
    return dict(re.findall(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;", block))


def test_every_interactive_element_is_a_native_labelled_control(console):
    root = parse(console)
    labels = {n.attrs["for"] for n in root.find_all("label") if "for" in n.attrs}
    inputs = [n for n in root.find_all("input") if n.attrs.get("type") != "hidden"]
    assert inputs, "the console has no inputs to check"
    for control in inputs:
        assert control.attrs.get("id") in labels, f"input {control.attrs} has no <label for>"
    for button in root.find_all("button"):
        assert button.text(), "a button with no text"
        assert button.attrs.get("type") == "submit"
    for link in root.find_all("a"):
        assert link.attrs.get("href") and link.text(), "a link with no destination or no text"
    for node in root.walk():
        assert not any(a.startswith("on") for a in node.attrs), f"inline script handler on <{node.tag}>"
        assert node.attrs.get("role") != "button", "a fake button: use <button>"
        if "tabindex" in node.attrs:
            assert int(node.attrs["tabindex"]) <= 0, "tabindex above zero breaks the natural keyboard order"
    for form in root.find_all("form"):
        assert form.attrs.get("method", "").lower() == "post" and form.attrs.get("action")


def test_the_page_has_the_landmarks_and_headings_a_keyboard_or_screen_reader_user_navigates_by(console):
    root = parse(console)
    assert root.find_all("html")[0].attrs.get("lang") == "en"
    assert root.find_all("title")[0].text()
    assert len(root.find_all("main")) == 1 and len(root.find_all("h1")) == 1
    levels = [int(n.tag[1]) for n in root.walk() if re.fullmatch(r"h[1-6]", n.tag)]
    assert all(b - a <= 1 for a, b in itertools.pairwise(levels)), f"a heading level is skipped: {levels}"
    first_link = root.find_all("a")[0]
    assert first_link.attrs["href"].startswith("#") and "skip" in first_link.classes  # the first Tab stop skips the navigation
    assert {t.attrs["scope"] for t in root.find_all("th")} == {"col"}  # table headers are declared


def test_focus_is_visible_in_the_stylesheet():
    css = CSS.read_text(encoding="utf-8")
    assert not re.search(r"outline\s*:\s*(none|0)\b", css), "an outline is switched off somewhere"
    rules = [(sel, body) for sel, body in re.findall(r"([^{}]*:focus[^{}]*){([^}]*)}", css) if "outline" in body]
    assert rules, "no :focus rule sets an outline"
    covered = " ".join(selector for selector, _ in rules)
    for element in ("button", "input", "a"):
        assert re.search(rf"(?:^|[\s,]){element}:focus", covered), f"{element} has no :focus outline"
    for _selector, body in rules:
        match = re.search(r"outline\s*:\s*(\d+)px\s+solid", body)
        assert match and int(match.group(1)) >= 2, "a focus outline thinner than 2px"


def test_text_and_background_contrast_is_at_least_4_5_to_1():
    v = variables()
    pairs = [
        ("fg", "bg"), ("fg", "panel"), ("muted", "bg"), ("muted", "panel"), ("button-fg", "button-bg"),
        ("notice-ok-fg", "notice-ok-bg"), ("notice-error-fg", "notice-error-bg"), ("link", "bg"), ("link", "panel"),
    ]
    for fore, back in pairs:
        assert contrast(v[fore], v[back]) >= 4.5, f"{fore} on {back} is {contrast(v[fore], v[back]):.2f}:1"
    assert contrast(v["focus"], v["bg"]) >= 3 and contrast(v["focus"], v["panel"]) >= 3  # a focus ring needs 3:1


def test_no_colour_is_used_in_the_stylesheet_outside_the_one_checked_palette():
    css = CSS.read_text(encoding="utf-8")
    outside = re.sub(r":root\s*{[^}]*}", "", css)
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(", outside), "a colour is declared outside :root, so the contrast test cannot see it"


@pytest.mark.covers("NFR-ACC-02-AC1")
def test_five_incidents_one_per_level_are_each_named_in_text_without_colour(console):
    root = parse(console)
    incidents = {n.attrs["data-proposal-id"]: n for n in root.find_all("article") if "data-proposal-id" in n.attrs}
    assert len(incidents) == 5
    named = {}
    for node in incidents.values():
        place = next(h.text() for h in node.walk() if h.tag == "h3")
        badge = [n for n in node.walk() if "severity" in n.classes]
        assert len(badge) == 1, "each incident states its severity exactly once, as an element of its own"
        named[place.split(": ")[1]] = spoken_text(badge[0])
    # "grayscale": the only thing read is the visible text of each severity element, never a class or a colour
    assert named == dict(zip(("Alpha St", "Bravo St", "Charlie St", "Delta St", "Echo St"), LEVELS, strict=True))
    for node in root.walk():
        assert "color" not in node.attrs.get("style", "").lower(), "colour set inline, outside the checked palette"


@pytest.mark.covers("NFR-ACC-02-AC1")
def test_each_level_also_has_its_own_symbol_so_the_levels_differ_by_shape_not_just_by_word(console):
    root = parse(console)
    legend = {n.text() for n in root.find_all("li") if "legend-item" in n.classes}
    symbols = {item.split(" ")[0] for item in legend}
    assert len(legend) == 5 and len(symbols) == 5, f"the five levels need five different symbols: {legend}"
    assert {item.split(" ", 1)[1] for item in legend} == set(LEVELS)
