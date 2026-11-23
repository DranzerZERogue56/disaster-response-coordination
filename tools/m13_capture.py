#!/usr/bin/env python3
"""m13_capture.py - run every command the README documents, in a fresh clone, and record the REAL output.

    python tools/m13_capture.py                  # clone the branch, run each documented command, write the record
    python tools/m13_capture.py --skip-tests     # same, without the 6-minute test suite
    python tools/m13_capture.py --branch main

Why it exists (Milestone 13 rule): an assistant may not be the source of a command, version, port or expected
output the author has not executed. The person running this script executes every command; the README is then
written from `docs/evidence/m13-command-outputs.md`, never from memory or guesswork.

It clones into a temporary folder (nothing in your working copy is touched), runs each step through bash, and
prints/records the exit code, the time and the last lines of output. Lines that carry a one-time password or
phone key are replaced with `[redacted]`. The app it starts is stopped at the end (port 8080 must be free).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from clean_machine_test import PORT, default_wait_healthy, find_bash, port_in_use, stop
from exe import find, path_of

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "evidence" / "m13-command-outputs.md"
SECRET_LINE = re.compile(r"(password|setup key|otpauth|secret)", re.I)
TAIL_LINES = 14


def tail(text, lines=TAIL_LINES):
    kept = [("[redacted]" if SECRET_LINE.search(line) else line) for line in text.strip().splitlines()]
    return "\n".join(kept[-lines:]) if kept else "(no output)"


def run_step(label, command, cwd, bash, results, timeout=900, head=False):
    started = time.monotonic()
    try:
        proc = subprocess.run([bash, "-c", command], cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)  # noqa: S603
        code, output = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        code, output = -1, f"(timed out after {timeout} s)"
    seconds = time.monotonic() - started
    shown = "\n".join(output.strip().splitlines()[:1]) if head else tail(output)
    results.append({"label": label, "command": command, "code": code, "seconds": seconds, "output": shown})
    print(f"[{'ok' if code == 0 else 'EXIT ' + str(code)}] {label}: {command} ({seconds:.1f} s)", flush=True)
    return code == 0


def http(path):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=5) as response:  # noqa: S310
            return f"HTTP {response.status} {response.read(300).decode('utf-8', 'replace').strip()}"
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code}"
    except OSError as exc:
        return f"failed: {exc}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", default="HW-submissions")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    if port_in_use():
        sys.exit(f"port {PORT} is already in use; stop that program and run again")
    url = subprocess.run([path_of("git"), "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()  # noqa: S603
    bash = find_bash()
    results = []
    work = Path(tempfile.mkdtemp(prefix="m13-capture-"))
    clone = work / "repo"
    py = 'source script/common.sh; "$PYTHON"'
    print(f"working in {work}\n", flush=True)

    run_step("version", "git --version", work, bash, results, head=True)
    run_step("version", "bash --version", work, bash, results, head=True)
    run_step("version", "python3 --version || python --version", work, bash, results, head=True)
    if find("ollama"):
        run_step("version (optional)", "ollama --version", work, bash, results, head=True)
    if run_step("clone", f"git clone --branch {args.branch} {url} repo", work, bash, results):
        run_step("version", "cd repo && git rev-parse HEAD", work, bash, results, head=True)
        ok = run_step("install", "./script/setup", clone, bash, results)
        run_step("version", f"{py} --version", clone, bash, results, head=True)
        if ok:
            for label, command in [("lint", "./script/lint"), ("secrets", "./script/secrets-check"), ("build", "./script/build"), ("smoke", "./script/smoke")]:
                run_step(label, command, clone, bash, results)
            run_step("create an account (secrets hidden)", f"{py} tools/enrol_dispatcher.py demo-dispatcher", clone, bash, results)
            run_step("put one proposal in front of the console", f"{py} tools/add_demo_proposal.py", clone, bash, results)
            app = subprocess.Popen([bash, "-c", "./script/start"], cwd=clone, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
            try:
                healthy = default_wait_healthy(90)
                results.append({"label": "run", "command": "./script/start, then GET /healthz", "code": 0 if healthy else 1, "seconds": 0.0, "output": http("/healthz")})
                results.append({"label": "run", "command": "GET /login (signed out)", "code": 0, "seconds": 0.0, "output": http("/login")[:120]})
                results.append({"label": "run", "command": "GET /dispatcher (signed out)", "code": 0, "seconds": 0.0, "output": http("/dispatcher")})
            finally:
                stop(app)
            if not args.skip_tests:
                run_step("test", "./script/test", clone, bash, results, timeout=1500)

    lines = [
        "# Command outputs recorded by `tools/m13_capture.py`",
        "",
        f"Run at {datetime.now(UTC).isoformat(timespec='seconds')} on {sys.platform}, Python {sys.version.split()[0]}, branch `{args.branch}`, in a fresh clone.",
        "Every block below is real output from commands the person running the script executed. Long output is trimmed to its last lines.",
        "",
    ]
    for r in results:
        lines += [f"## {r['label']}: `{r['command']}`", "", f"Exit code {r['code']}, {r['seconds']:.1f} s.", "", "```", r["output"], "```", ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    failed = [r for r in results if r["code"] != 0]
    print(f"\nwrote {OUT}; {len(results)} steps, {len(failed)} failed")
    os.chdir(ROOT)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
