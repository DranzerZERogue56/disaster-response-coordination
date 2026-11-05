# Manual test MANUAL-ACC-01: keyboard-only pass on the dispatcher console

**Criterion:** NFR-ACC-01-AC1. Every dispatcher action in the web UI (approve, modify, reject, override) is reachable and operable by keyboard alone, with a visible focus indicator at every step.

**How it is measured (from `docs/requirements.md`):** a manual pass with the mouse unplugged: complete all four actions on a seeded proposal, confirming focus is visible after every keypress.

**Who runs it:** Ben, by hand. The assistant cannot press keys for you and cannot judge whether a focus outline is visible on your screen. A pass that nobody watched would be a made-up result.

**Time:** about 15 minutes.

## Before you start

1. Close every other app window that could steal focus. Use one browser (Edge or Chrome). Write down the browser name and version in the evidence file.
2. In a terminal in the repo folder, prepare the data. This builds a fresh database with three proposals waiting and one assignment in force, and prints the start command:

   ```
   python tools/prepare_accessibility_pass.py
   ```

3. Start the app exactly as it prints (Git Bash):

   ```
   DB_PATH="data/acc01.sqlite" ./script/start
   ```

   Leave that terminal alone. Check `http://127.0.0.1:8080/healthz` in the browser says `{"status": "ok"}`, then **take your hands off the mouse**: unplug it, or turn the touchpad off (Windows: Settings, Bluetooth and devices, Touchpad, off). From here on, keyboard only.
4. Optional but better evidence: start a screen recording (Windows: Win + Alt + R records the window). If you record, save it under `tests/manual/evidence/` and name it in the evidence file. Large videos: tell the assistant before committing it.

## Keys you may use

Tab, Shift + Tab, Enter, Space, the number keys, letters (to type a reason), Ctrl + L (to type the address). Nothing else. If you catch yourself reaching for the mouse, write that down as a failure of that step.

## The steps

For **every** key press below, look at the screen and ask: *can I see which control has focus (an outline around it)?* Write Y or N in the table of your evidence file. One N anywhere means the result is **fail**.

| # | Do this | You should see |
|---|---|---|
| 1 | Press Ctrl + L, type `127.0.0.1:8080/dispatcher`, press Enter | The Dispatcher console. Three proposals are waiting (each with Approve, Modify, Reject), one assignment is in force (with an Override form), and a Units table. |
| 2 | Press Tab once | A link "Skip to the proposals waiting for a decision" appears with a thick outline. |
| 3 | Press Enter | The page jumps to the proposals. |
| 4 | Press Tab until the outline is on the first button, "Approve proposal 2" (count the presses) | A thick outline around the button each time you press Tab. |
| 5 | Press Enter | The page reloads with a green box at the top: "Proposal 2 approved; unit N notified." |
| 6 | Press Tab (the page starts again from the top, which is expected) until you reach the box "Unit number to send instead" for **proposal 3** | A thick outline around the box. Read the Units table first if you need a unit number (see the note below). |
| 7 | Type the number of a unit that says **available** in the Units table and is **not** the unit named in that proposal ("unit N proposed") | Your digits appear in the box. |
| 8 | Press Tab, then Enter on "Modify proposal 3" | Green box: "Proposal 3 modified: unit N assigned instead." |
| 9 | Press Tab until "Reject proposal 4", then Enter | Green box: "Proposal 4 rejected; its unit was freed." |
| 10 | Press Tab until "New unit number" under **Assignments in force**, type the number of an available unit | The outline is on the box and the digits appear. |
| 11 | Press Tab, type a reason such as `keyboard pass`, press Tab, then Enter on "Override assignment 1" | Green box: "Assignment for proposal 1 moved to unit N." |
| 12 | Press Shift + Tab several times | The outline moves backwards through the controls and stays visible. |
| 13 | Press Tab until you reach the link "Refresh this page" and press Enter | The page reloads and shows all four decisions made: no proposals waiting. |

Note on step 7: the Units table is in the "Units" section. If you cannot find a free unit number without scrolling, press Tab to the navigation link "Units" (near the top) and press Enter to jump there, then Tab back. That counts as part of the pass.

## What counts as a pass

All of these:

- All four actions (approve, modify, reject, override) were completed with the keyboard only.
- Focus was visible after every key press (every row of your table says Y).
- You never needed the mouse.

Anything else is a **fail**, and a fail is a useful result: it goes in the defect log with severity and a reason, and the matrix will show NFR-ACC-01 as failing rather than passing. Do not repeat the pass until it succeeds and report only the last attempt; record the first full attempt.

## Your evidence file

Copy this into `tests/manual/evidence/acc-01-keyboard-only-YYYY-MM-DD.md` and fill it in as you go (the date is the day you run it):

```
# MANUAL-ACC-01 evidence

- Tester: Ben
- Date and start time:
- Browser and version:
- Mouse unplugged or touchpad off: yes / no
- Screen recording file (if any):

| Step | Keys pressed | What had focus | Outline visible (Y/N) |
|---|---|---|---|
| 2 | Tab | | |
| 4 | Tab x __ | Approve proposal 2 | |
| 5 | Enter | | |
| 6 | Tab x __ | modify box, proposal 3 | |
| 7 | digits | | |
| 8 | Tab, Enter | Modify proposal 3 | |
| 9 | Tab x __, Enter | Reject proposal 4 | |
| 10 | Tab x __, digits | new unit box | |
| 11 | Tab, text, Tab, Enter | Override assignment 1 | |
| 12 | Shift+Tab x __ | | |
| 13 | Tab x __, Enter | Refresh link | |

Result (pass / fail):
Anything that surprised me, was awkward, or made me want the mouse:
```

## Recording the result

When you have the evidence file, record it. Use `pass` or `fail` honestly:

```
python tools/record_manual_result.py --id MANUAL-ACC-01 --criteria NFR-ACC-01-AC1 --status pass --tester Ben --evidence tests/manual/evidence/acc-01-keyboard-only-YYYY-MM-DD.md
```

The tool refuses if the evidence file does not exist. Then tell the assistant, who regenerates the matrix.

## Known limits, so you are not surprised

- After you press a button, the browser reloads the page and focus starts again from the top. That is how a plain form works; it is why step 6 says to Tab again. It is not counted as a failure unless the outline is not visible.
- There is no sign-in yet (a stand-in dispatcher is used), so there is nothing about login to test.
- Screen-reader behaviour is not part of this criterion.
