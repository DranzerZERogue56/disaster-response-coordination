#!/usr/bin/env python3
"""auto_demo.py - run the Milestone 10 demo by itself: type each command into
this terminal, really run it against the real app, speak a narration, and
(optionally) record the window.

Everything it says and runs comes from docs/demo/auto-demo-script.json. Edit
that file to change the demo; no code change is needed.

Modes (nothing is recorded unless you pass --record):

    python tools/auto_demo.py                 rehearsal: types and runs every
                                              command, prints the narration,
                                              no voice, no recording, fast
    python tools/auto_demo.py --tts-only      make the voice clips, print how
                                              long each takes, write the
                                              captions file; no commands run
    python tools/auto_demo.py --record        the real thing: voice + window
                                              recording + captions
    python tools/auto_demo.py --record --full-screen
                                              record the whole desktop instead
                                              of just this window (shows
                                              anything else on screen!)

How the recording is made: ffmpeg captures this window; the voice is Windows'
built-in speech (System.Speech) rendered to audio files; the audio is laid
onto the video at the moment each step started and the two are joined. The
video says out loud, at the start, that the voice is a computer voice.

The demo uses its own database (data/demo.sqlite) and port 8080, never your
development database.
"""
import argparse
import ctypes
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "docs" / "demo" / "auto-demo-script.json"
CAPTIONS = ROOT / "docs" / "demo" / "iteration-1-demo.srt"
DEMO_DB = "data/demo.sqlite"
PORT = 8080
WINDOW_TITLE = "IterationOneDemo"
CAPTURE_LATENCY = 0.6  # seconds ffmpeg takes to begin capturing after launch
TYPE_DELAY = 0.03
DIM, CYAN, RESET = "\033[2m", "\033[36m", "\033[0m"


def demo_env():
    env = {**os.environ}
    env["DB_PATH"] = DEMO_DB
    env["SWEEP_SECONDS"] = "5"
    env["PYTHONUTF8"] = "1"
    env["PATH"] = str(ROOT / ".venv" / "Scripts") + os.pathsep + env.get("PATH", "")
    return env


def load_steps():
    return json.loads(SCRIPT.read_text(encoding="utf-8"))["steps"]


# ---------------------------------------------------------------- the voice
def synthesize(steps, outdir):
    """Render every 'say' to a WAV with Windows' built-in voice."""
    for i, step in enumerate(steps):
        (outdir / f"{i:02d}.txt").write_text(step["say"], encoding="utf-8")
    ps1 = outdir / "synth.ps1"
    ps1.write_text(
        "Add-Type -AssemblyName System.Speech\n"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "$s.Rate = 0\n"
        "Get-ChildItem -Path $args[0] -Filter *.txt | ForEach-Object {\n"
        "  $s.SetOutputToWaveFile(($_.FullName -replace '\\.txt$','.wav'))\n"
        "  $s.Speak([IO.File]::ReadAllText($_.FullName))\n"
        "}\n"
        "$s.Dispose()\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), str(outdir)],
        check=True,
        capture_output=True,
    )
    clips = []
    for i in range(len(steps)):
        path = outdir / f"{i:02d}.wav"
        with wave.open(str(path), "rb") as w:
            clips.append((path, w.getnframes() / w.getframerate()))
    return clips


def build_audio(events, clips, lead_seconds, out_path):
    """One WAV the length of the video: silence, with each clip placed where
    its step started."""
    with wave.open(str(clips[0][0]), "rb") as first:
        params = first.getparams()
    frame_bytes = params.nchannels * params.sampwidth
    with wave.open(str(out_path), "wb") as out:
        out.setparams(params)
        written = 0.0
        for event, (path, duration) in zip(events, clips, strict=True):
            start = max(written, event["start"] + lead_seconds)
            silence = int((start - written) * params.framerate)
            out.writeframes(b"\x00" * silence * frame_bytes)
            with wave.open(str(path), "rb") as clip:
                out.writeframes(clip.readframes(clip.getnframes()))
            written = start + duration
        out.writeframes(b"\x00" * int(1.0 * params.framerate) * frame_bytes)


def write_captions(events, lead_seconds, path):
    """An .srt: each narration split into sentences, timed in proportion."""

    def stamp(t):
        t = max(0.0, t)
        ms = round(t * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    cues = []
    for ev in events:
        sentences = [s.strip() for s in ev["text"].replace("? ", "?|").replace(". ", ".|").split("|") if s.strip()]
        total = sum(len(s) for s in sentences) or 1
        cursor = ev["start"] + lead_seconds
        for s in sentences:
            span = ev["duration"] * len(s) / total
            cues.append((cursor, cursor + span, s))
            cursor += span
    lines = []
    for n, (a, b, text) in enumerate(cues, 1):
        lines += [str(n), f"{stamp(a)} --> {stamp(b)}", "\n".join(textwrap.wrap(text, 60)), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------- the show
def caption(text):
    print(f"{CYAN}", end="")
    for line in textwrap.wrap(text, 100):
        print(f"  [voice] {line}")
    print(RESET, end="", flush=True)


def type_command(cmd, fast):
    sys.stdout.write("$ ")
    for ch in cmd:
        sys.stdout.write(ch)
        sys.stdout.flush()
        if not fast:
            time.sleep(TYPE_DELAY)
    sys.stdout.write("\n")
    sys.stdout.flush()


def run_command(cmd, env):
    proc = subprocess.Popen(
        ["bash", "-c", cmd],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    return proc.wait()


def start_server(env):
    if socket.socket().connect_ex(("127.0.0.1", PORT)) == 0:
        sys.exit(f"Port {PORT} is already in use; stop whatever is running there and try again.")
    server = subprocess.Popen(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "flask", "--app", "src.web_ui.app",
         "run", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        if socket.socket().connect_ex(("127.0.0.1", PORT)) == 0:
            print(f"{DIM}  (application started on port {PORT}){RESET}")
            return server
        time.sleep(0.25)
    server.kill()
    sys.exit("The application did not start.")


def play(steps, clips, env, fast, t0):
    """Run every step. Returns the timeline [{start, text, duration}]."""
    events = []
    server = None
    try:
        for i, step in enumerate(steps):
            start = time.time() - t0
            duration = clips[i][1] if clips else 0.0
            events.append({"start": start, "text": step["say"], "duration": duration})
            caption(step["say"])
            if not fast:
                time.sleep(0.8)
            if step.get("action") == "start_server":
                server = start_server(env)
            if step.get("run"):
                type_command(step["run"], fast)
                code = run_command(step["run"], env)
                if code != 0:
                    print(f"{DIM}  (command exited with code {code}){RESET}")
            if not fast:
                remaining = duration - ((time.time() - t0) - start)
                time.sleep(max(0.0, remaining) + step.get("pause", 0.5))
            print()
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
    return events


def prepare_database(env):
    path = ROOT / DEMO_DB
    path.parent.mkdir(exist_ok=True)
    path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--record", action="store_true", help="record the window with the voice")
    parser.add_argument("--tts-only", action="store_true", help="only make the voice clips and captions")
    parser.add_argument("--full-screen", action="store_true", help="record the whole desktop")
    parser.add_argument("--out", default=str(Path.home() / "Videos" / "iteration-1-demo.mp4"))
    args = parser.parse_args()

    steps = load_steps()
    env = demo_env()
    ctypes.windll.kernel32.SetConsoleTitleW(WINDOW_TITLE)

    if args.tts_only:
        with tempfile.TemporaryDirectory() as tmp:
            clips = synthesize(steps, Path(tmp))
            events, cursor = [], 0.0
            for step, (_, dur) in zip(steps, clips, strict=True):
                events.append({"start": cursor, "text": step["say"], "duration": dur})
                cursor += dur + step.get("pause", 0.5) + 1.5
            write_captions(events, 0.0, CAPTIONS)
            for step, (_, dur) in zip(steps, clips, strict=True):
                print(f"{dur:5.1f}s  {step['id']}")
            print(f"narration alone: {sum(d for _, d in clips):.0f}s. captions: {CAPTIONS}")
        return

    prepare_database(env)

    if not args.record:
        print(f"{DIM}REHEARSAL: nothing is recorded and there is no voice.{RESET}\n")
        play(steps, None, env, fast=True, t0=time.time())
        (ROOT / DEMO_DB).unlink(missing_ok=True)
        return

    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg is not on PATH.")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        print("Making the voice clips...")
        clips = synthesize(steps, tmp)
        for n in (3, 2, 1):
            print(f"Recording starts in {n}... (do not touch the mouse or keyboard, keep this window visible)")
            time.sleep(1)
        os.system("cls")

        source = "desktop" if args.full_screen else f"title={WINDOW_TITLE}"
        video = tmp / "video.mp4"
        launch = time.time()
        ffmpeg = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "gdigrab", "-framerate", "15", "-i", source,
             "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", str(video)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2.0)
        t0 = time.time()
        lead = (t0 - launch) - CAPTURE_LATENCY
        try:
            events = play(steps, clips, env, fast=False, t0=t0)
            time.sleep(1.5)
        finally:
            ffmpeg.stdin.write(b"q")
            ffmpeg.stdin.flush()
            ffmpeg.wait(timeout=60)
            (ROOT / DEMO_DB).unlink(missing_ok=True)

        audio = tmp / "voice.wav"
        build_audio(events, clips, lead, audio)
        write_captions(events, lead, CAPTIONS)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video), "-i", str(audio), "-c:v", "copy", "-c:a", "aac",
             "-b:a", "128k", "-shortest", str(out_path)],
            check=True,
            capture_output=True,
        )
    print(f"\nRecording saved: {out_path}\nCaptions: {CAPTIONS}")


if __name__ == "__main__":
    main()
