# Command outputs recorded by `tools/m13_capture.py`

Run at 2026-11-23T04:16:02+00:00 on win32, Python 3.11.8, branch `HW-submissions`, in a fresh clone.
Every block below is real output from commands the person running the script executed. Long output is trimmed to its last lines.

## version: `git --version`

Exit code 0, 0.1 s.

```
git version 2.46.0.windows.1
```

## version: `bash --version`

Exit code 0, 0.1 s.

```
GNU bash, version 5.2.26(1)-release (x86_64-pc-msys)
```

## version: `python3 --version || python --version`

Exit code 0, 0.1 s.

```
Python 3.11.8
```

## version (optional): `ollama --version`

Exit code 0, 0.1 s.

```
ollama version is 0.40.16
```

## clone: `git clone --branch HW-submissions https://github.com/DranzerZERogue56/disaster-response-coordination.git repo`

Exit code 0, 1.6 s.

```
Cloning into 'repo'...
```

## version: `cd repo && git rev-parse HEAD`

Exit code 0, 0.1 s.

```
3c944066d8696cd331b7920ee57960a600a30444
```

## install: `./script/setup`

Exit code 0, 75.6 s.

```

[notice] A new release of pip is available: 26.2.2 -> 26.3
[notice] To update, run: C:\Users\mercu\AppData\Local\Temp\m13-capture-yqlnfr3v\repo\.venv\Scripts\python.exe -m pip install --upgrade pip
  apply 0001  0001-initial.sql
  apply 0002  0002-assigned-requires-approved.sql
  apply 0003  0003-override-follow-ups.sql
  apply 0004  0004-proposal-input-data.sql
  apply 0005  0005-heartbeat-alerts.sql
  apply 0006  0006-tiebreak-log-and-escalations.sql
  apply 0007  0007-incident-versions.sql
  apply 0008  0008-unit-status-broadcast.sql
  apply 0009  0009-two-factor-login.sql
migrate.py: 9 migration(s) applied, database at data/dev.sqlite
setup complete
```

## version: `source script/common.sh; "$PYTHON" --version`

Exit code 0, 0.1 s.

```
Python 3.11.8
```

## lint: `./script/lint`

Exit code 0, 1.1 s.

```
All checks passed!
```

## secrets: `./script/secrets-check`

Exit code 0, 2.4 s.

```
secrets check: 0 matches across 325 tracked files
```

## build: `./script/build`

Exit code 0, 1.2 s.

```
build ok
```

## smoke: `./script/smoke`

Exit code 0, 1.1 s.

```
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\mercu\AppData\Local\Temp\m13-capture-yqlnfr3v\repo\.venv\Lib\site-packages\flask\app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\mercu\AppData\Local\Temp\m13-capture-yqlnfr3v\repo\src\web_ui\app.py", line 276, in healthz
    conn = connect()
           ^^^^^^^^^
  File "C:\Users\mercu\AppData\Local\Temp\m13-capture-yqlnfr3v\repo\src\db.py", line 14, in connect
    conn = sqlite3.connect(get_db_path())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: unable to open database file
smoke: /healthz is healthy against a real data store
smoke: /healthz correctly fails when the data store is unavailable (500)
smoke: all checks passed
```

## seed the demo data (units and one run): `./script/seed`

Exit code 0, 0.4 s.

```
skip  0001  0001-initial.sql (already applied)
  skip  0002  0002-assigned-requires-approved.sql (already applied)
  skip  0003  0003-override-follow-ups.sql (already applied)
  skip  0004  0004-proposal-input-data.sql (already applied)
  skip  0005  0005-heartbeat-alerts.sql (already applied)
  skip  0006  0006-tiebreak-log-and-escalations.sql (already applied)
  skip  0007  0007-incident-versions.sql (already applied)
  skip  0008  0008-unit-status-broadcast.sql (already applied)
  skip  0009  0009-two-factor-login.sql (already applied)
migrate.py: 0 migration(s) applied, database at data/dev.sqlite
seed complete
```

## create an account (secrets hidden): `source script/common.sh; "$PYTHON" tools/enrol_dispatcher.py demo-dispatcher`

Exit code 0, 0.3 s.

```
Account ready: demo-dispatcher (dispatcher) in data/dev.sqlite
[redacted]
[redacted]
[redacted]
Then start the app with ./script/start and sign in at http://127.0.0.1:8080/login
```

## put one proposal in front of the console: `source script/common.sh; "$PYTHON" tools/add_demo_proposal.py`

Exit code 0, 0.8 s.

```
Proposal 1 is waiting for a person (unit 1 is held for it).
Open http://127.0.0.1:8080/dispatcher, sign in, and approve it within 4 minutes.
```

## run: `./script/start, then GET /healthz`

Exit code 0, 0.0 s.

```
HTTP 200 {"status":"ok"}
```

## run: `GET /login (signed out)`

Exit code 0, 0.0 s.

```
HTTP 200 <!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-
```

## run: `GET /dispatcher (signed out)`

Exit code 0, 0.0 s.

```
HTTP 401
```

## test: `./script/test`

Exit code 0, 441.1 s.

```
src\negotiation\service.py                 93      3    97%   30-31, 88
src\notify_responder\service.py            21      1    95%   73
src\override_assignment\service.py         48      2    96%   42-43
src\unit_registry\broadcast.py             19      1    95%   18
src\unit_registry\service.py              115      8    93%   152, 160, 167, 171, 196, 206, 212-213
src\web_ui\actions.py                      28      4    86%   22-23, 48-49
src\web_ui\app.py                         303     27    91%   101, 165-166, 193-205, 215-218, 248, 254, 434-437, 451-452, 522
src\web_ui\dispatcher.py                   91      4    96%   60, 155, 187-188
---------------------------------------------------------------------
TOTAL                                    1760     67    96%

28 files skipped due to complete coverage.
Required test coverage of 90% reached. Total coverage: 96.19%
======================= 820 passed in 439.67s (0:07:19) =======================
```
