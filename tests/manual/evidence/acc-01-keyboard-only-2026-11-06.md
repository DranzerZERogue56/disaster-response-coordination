# MANUAL-ACC-01 evidence

- Tester: Ben (Dranzer Rogue)
- Date: 2026-11-06 (reported to the assistant that day; the assistant did not watch the pass)
- Script followed: `tests/manual/scripts/acc-01-keyboard-only.md`, on data prepared by `tools/prepare_accessibility_pass.py`
- Result: **pass**

## What the tester reported

In the tester's words: "I did the keyboard pass, I like it, it worked well."

## What this record does and does not contain

This is a self-reported summary. The per-step table from the script (which control had focus, outline visible Y or N, for each key press) was **not filled in**, the browser name and version were not recorded, and no screen recording was kept. So the record supports "the tester completed the four actions with the keyboard and was satisfied with focus visibility", but it cannot show step by step that focus was visible after every key press, which is the wording of NFR-ACC-01.

The automated checks that support the same criterion are separate and are in the suite: every control is a native labelled control, no tabindex above zero, the stylesheet sets a 3 px focus outline on links, buttons and inputs, and all four actions work through the page forms on the prepared data (`tests/unit/test_dispatcher_accessibility.py`, `tests/integration/test_dispatcher_ui_http.py`, `tests/unit/test_prepare_accessibility_pass.py`).

## To strengthen this record (optional, tester to do)

Add under this heading: the browser and version; any step where an outline was hard to see; anything that made the tester want the mouse.
