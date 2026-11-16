# NFR-MNT-01 clean-machine run

- Date: 2026-11-15
- Commit cloned: `a59029b`
- README steps followed: `./script/setup`, `./script/start`
- Time from first step to a healthy app: **84.2 s** (limit 300 s)
- Result: **PASS**
- Model download time: not applicable (the README's Run it steps need no model; the optional Ollama model is a separate step).
- Limits: run on the developer's laptop from a fresh clone, with Python already installed and a warm pip cache. It proves the README's steps work from a clean checkout; the Week 13 clean-machine test repeats it on a machine that has never seen the project.

## Earlier run the same day (kept for honesty)

An earlier run on 2026-11-15 reported FAIL (evidence kept in `mnt-01-clean-machine-2026-11-15-run1-FAILED.md`): a server left over from an earlier run of this same tool held port 8080, a fault of the test tooling and not of the app, so it is not counted as a result about the app in `tests/manual/results.csv`. The tool now refuses to start when the port is busy and ends the server it starts. Passing runs followed (77.3 s, 94.8 s and this one, 84.2 s at commit `a59029b`, the final code of v0.9.0-rc.2, with the sign-in on).
