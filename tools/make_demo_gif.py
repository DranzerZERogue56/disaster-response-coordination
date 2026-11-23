#!/usr/bin/env python3
"""make_demo_gif.py - record the sign-in-and-approve flow as an animated GIF (docs/demo/signin-and-approve.gif).

    python tools/make_demo_gif.py

Optional tool: it needs Playwright with Chromium and Pillow, which are NOT part of requirements*.txt (the app and
the test suite do not need them). Install them yourself if you want to re-record:
    python -m pip install playwright pillow && python -m playwright install chromium

What it does: builds a throwaway database in a temp folder, creates a throwaway dispatcher account, puts one waiting
proposal on the console, starts the real app on port 8099 with the sign-in on, drives a headless browser through
sign-in and Approve, takes a screenshot after each step, captions the frames and joins them into the GIF. The password
and phone key belong to the throwaway account and are never written anywhere. The app it starts is stopped at the end.
"""
import glob
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo" / "signin-and-approve.gif"
PORT = 8099
BASE = f"http://127.0.0.1:{PORT}"


def project_python():
    """The project's own virtual environment (it has Flask and the other pinned packages); Playwright runs in the caller's Python."""
    for candidate in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python"):
        if candidate.exists():
            return str(candidate)
    sys.exit("run ./script/setup first: the project's virtual environment (.venv) does not exist")


def make_database(path):
    conn = sqlite3.connect(path)
    for migration in sorted(glob.glob(str(ROOT / "migrations" / "*.sql"))):
        conn.executescript(Path(migration).read_text(encoding="utf-8"))
    conn.executescript((ROOT / "seed" / "iteration-1.sql").read_text(encoding="utf-8"))
    conn.close()
    code = (
        "import json, sqlite3, sys; sys.path.insert(0, '.'); from src.auth.service import enrol; "
        f"c = sqlite3.connect(r'{path}'); c.row_factory = sqlite3.Row; a = enrol(c, 'demo-dispatcher', 'dispatcher'); "
        "print(json.dumps({'password': a['password'], 'totp_secret': a['totp_secret']}))"
    )
    import json

    out = subprocess.run([project_python(), "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)  # noqa: S603
    return json.loads(out.stdout.strip().splitlines()[-1])


def phone_code(secret):
    code = f"import sys, time; sys.path.insert(0, '.'); from src.auth.totp import code_at, step_for; print(code_at('{secret}', step_for(time.time())))"
    return subprocess.run([project_python(), "-c", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()  # noqa: S603


def wait_healthy(seconds=30):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/healthz", timeout=2) as response:  # noqa: S310
                if response.status == 200:
                    return True
        except OSError:
            time.sleep(0.3)
    return False


def caption(png_path, text, size=(900, 600)):
    from PIL import Image, ImageDraw, ImageFont

    shot = Image.open(png_path).convert("RGB").resize(size)
    band = Image.new("RGB", (size[0], 44), (20, 40, 80))
    draw = ImageDraw.Draw(band)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    draw.text((14, 9), text, fill=(255, 255, 255), font=font)
    frame = Image.new("RGB", (size[0], size[1] + 44))
    frame.paste(band, (0, 0))
    frame.paste(shot, (0, 44))
    return frame


def main():
    from playwright.sync_api import sync_playwright

    tmp = Path(tempfile.mkdtemp(prefix="demo-gif-"))
    db = tmp / "demo.sqlite"
    account = make_database(db)
    env = {**os.environ, "DB_PATH": str(db), "AUTH_ENFORCED": "1", "SWEEP_SECONDS": "1", "PYTHONPATH": str(ROOT)}
    subprocess.run([project_python(), str(ROOT / "tools" / "add_demo_proposal.py"), str(db)], env=env, cwd=ROOT, check=True, capture_output=True)  # noqa: S603
    server = subprocess.Popen(  # noqa: S603
        [project_python(), "-m", "flask", "--app", "src.web_ui.app", "run", "--host", "127.0.0.1", "--port", str(PORT)],
        env=env,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    frames = []
    try:
        if not wait_healthy():
            sys.exit("the app did not start on port 8099 (is something else using it?)")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1000, "height": 700})
            shots = tmp / "shots"
            shots.mkdir()

            def snap(name, text):
                path = shots / f"{name}.png"
                page.screenshot(path=str(path))
                frames.append(caption(path, text))

            page.goto(f"{BASE}/login")
            snap("1", "1. Open the sign-in page at http://127.0.0.1:8080/login")
            page.fill("#username", "demo-dispatcher")
            page.fill("#password", account["password"])
            page.fill("#code", phone_code(account["totp_secret"]))
            snap("2", "2. Enter the username, the password and the six-digit phone code")
            page.click("button[type=submit]")
            page.wait_for_load_state()
            page.goto(f"{BASE}/dispatcher")
            snap("3", "3. Signed in: one proposal is waiting for a person (4-minute hold)")
            page.click("text=Approve proposal")
            page.wait_for_load_state()
            snap("4", "4. After Approve: the proposal leaves the waiting list and the unit is assigned")
            browser.close()
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(server.pid)], capture_output=True, check=False) if sys.platform == "win32" else server.terminate()  # noqa: S603, S607
    OUT.parent.mkdir(parents=True, exist_ok=True)
    palette = [f.convert("P", palette=1, colors=64) for f in frames]
    palette[0].save(OUT, save_all=True, append_images=palette[1:], duration=2600, loop=0, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
