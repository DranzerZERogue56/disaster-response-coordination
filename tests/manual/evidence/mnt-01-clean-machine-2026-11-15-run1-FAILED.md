# NFR-MNT-01 clean-machine run

- Date: 2026-11-15
- Commit cloned: `b925c00`
- README steps followed: `./script/setup`, `./script/start`
- Time from first step to a healthy app: **139.8 s** (limit 300 s)
- Result: **FAIL** (failed at: healthz never answered)
- Model download time: not applicable (the README's Run it steps need no model; the optional Ollama model is a separate step).
- Limits: run on the developer's laptop from a fresh clone, with Python already installed and a warm pip cache. It proves the README's steps work from a clean checkout; the Week 13 clean-machine test repeats it on a machine that has never seen the project.

## Why this run failed (added by the assistant, 2026-11-15)

A server left over from an earlier run of this same tool was still holding port 8080 (the tool's stop step ended the launcher but not the server underneath), so this run's app could not start and `/healthz` never answered. It was a fault of the test tooling, not of the app. The leftover processes were identified and stopped, the tool was changed to refuse to start if the port is busy and to end its own leftover servers, and the run was repeated; see `mnt-01-clean-machine-2026-11-15.md`.
