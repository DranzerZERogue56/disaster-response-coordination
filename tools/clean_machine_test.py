#!/usr/bin/env python3
"""clean_machine_test.py - NFR-MNT-01: a clean clone reaches a running app in under 5 minutes
using only the README.

    python tools/clean_machine_test.py            # clone, follow the README, time it, record it

It clones this repository into a fresh temporary folder, runs exactly the commands the README's
"Run it" block lists (today: ./script/setup, then ./script/start), waits for GET /healthz to answer
{"status": "ok"}, and stops the app it started. The clock runs from the first README command to the
first healthy answer. Under 300 seconds is a pass. The result and a short evidence file are written to
tests/manual/evidence/ and recorded in tests/manual/results.csv (see tools/record_manual_result.py).
Model download time would be recorded separately; this release has no model to download.

The functions take their collaborators (command runner, app starter, health check, clock) as arguments so
the logic is tested with fakes, without a five-minute install.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIMIT_SECONDS = 300
PORT = 8080


def readme_steps(readme_text):
    """The commands in the README's 'Run it' fenced block, in order (lines that start with ./script/)."""
    section = re.search(r"## Run it(.*?)(?=\n## )", readme_text, re.S)
    block = re.search(r"```\n(.*?)```", section.group(1), re.S)
    return [line.split("#")[0].strip() for line in block.group(1).splitlines() if line.strip().startswith("./script/")]


def find_bash():
    git = shutil.which("git")
    candidates = []
    if git:
        root = Path(git).resolve().parent.parent
        candidates += [root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"]
    candidates += [Path(r"C:\Program Files\Git\bin\bash.exe")]
    for c in candidates:
        if c.exists():
            return str(c)
    return shutil.which("bash") or "bash"


def default_run(command, cwd):
    return subprocess.run([find_bash(), "-c", command], cwd=cwd, capture_output=True, text=True, check=False).returncode == 0


def default_start(command, cwd):
    return subprocess.Popen([find_bash(), "-c", command], cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop(app):
    """Stop the app and everything it started. The app is launched through bash, so ending only the
    bash process would leave Python running and holding files open in the clone (on Windows that
    makes the clean-up fail); on Windows the whole process tree is ended."""
    if app is None or not hasattr(app, "terminate"):
        return
    pid = getattr(app, "pid", None)
    if sys.platform == "win32" and pid:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, check=False)
    else:
        app.terminate()


def default_wait_healthy(timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/healthz", timeout=2) as resp:
                if json.loads(resp.read()) == {"status": "ok"}:
                    return True
        except OSError:
            time.sleep(0.5)
    return False


def run(readme_text, workdir, run_command=default_run, start_app=default_start, wait_healthy=default_wait_healthy, clock=time.monotonic):
    """Follow the README in `workdir`. Returns {"seconds", "steps", "ok", "failed_step"}."""
    steps = readme_steps(readme_text)
    started = clock()
    done = []
    app = None
    try:
        for step in steps:
            if step.endswith("/start"):
                app = start_app(step, workdir)  # a server: runs until stopped, so it is not waited for
                ok = True
            else:
                ok = run_command(step, workdir)
            done.append(step)
            if not ok:
                return {"seconds": clock() - started, "steps": done, "ok": False, "failed_step": step}
        healthy = wait_healthy()
        seconds = clock() - started
        return {
            "seconds": seconds,
            "steps": done,
            "ok": bool(healthy) and seconds < LIMIT_SECONDS,
            "failed_step": None if healthy else "healthz never answered",
        }
    finally:
        stop(app)


def main():
    import os

    from record_manual_result import record

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        clone = Path(tmp) / "clean-clone"
        cloned = subprocess.run(["git", "clone", "--quiet", str(ROOT), str(clone)], capture_output=True, text=True, check=False)
        if cloned.returncode != 0:
            sys.exit("clone failed: " + cloned.stderr)
        os.environ.pop("DB_PATH", None)  # a clean machine has no leftover settings
        result = run((clone / "README.md").read_text(encoding="utf-8"), clone)

    evidence = ROOT / "tests" / "manual" / "evidence" / f"mnt-01-clean-machine-{date.today().isoformat()}.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        "# NFR-MNT-01 clean-machine run\n\n"
        f"- Date: {date.today().isoformat()}\n- Commit cloned: `{subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()}`\n"
        f"- README steps followed: {', '.join(f'`{s}`' for s in result['steps'])}\n"
        f"- Time from first step to a healthy app: **{result['seconds']:.1f} s** (limit {LIMIT_SECONDS} s)\n"
        f"- Result: **{'PASS' if result['ok'] else 'FAIL'}**" + (f" (failed at: {result['failed_step']})" if result["failed_step"] else "") + "\n"
        "- Model download time: not applicable (no model is downloaded in this release).\n",
        "- Limits: run on the developer's laptop from a fresh clone, with Python already installed and a warm pip cache. It proves the README's steps work from a clean checkout; the Week 13 clean-machine test repeats it on a machine that has never seen the project.\n",
        encoding="utf-8",
    )
    record("MANUAL-MNT-01", "NFR-MNT-01-AC1", "pass" if result["ok"] else "fail", "clean_machine_test.py", str(evidence.relative_to(ROOT)).replace("\\", "/"))
    print(f"{'PASS' if result['ok'] else 'FAIL'}: {result['seconds']:.1f} s; evidence {evidence.relative_to(ROOT)}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
