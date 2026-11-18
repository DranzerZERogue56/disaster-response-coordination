# Security review: fact sheet (input for Ben)

Neutral observations only. This file contains no conclusions, no dispositions and no severities; those belong in `docs/security-review.md`, which Ben writes. Each observation says what, where (file:line), and how to re-run it. Gathered 2026-11-15 at the working tree of `main` (uncommitted changes present in `docs/`; no source file changed by this fact sheet). All commands run from the repo root; `PY=./.venv/Scripts/python`.

Observation IDs (F1.1, F2.3, ...) are for you to cite.

---

## 1. Secrets

| ID | Observation | How to re-run |
|---|---|---|
| F1.1 | `./script/secrets-check` ran `tools/secrets_scan.py` over `git ls-files`. Output: `secrets check: 0 matches across 259 tracked files`. | `./script/secrets-check` |
| F1.2 | The pattern list (`tools/secrets_scan.py:12-19`): `api_key`/`api-key`, `secret_key`, `password\s*=`, `AKIA` + 16 chars, PEM private-key headers, `token\s*=\s*"..."` (10+ chars), `ghp_` + 20+ chars, `sk-` + 20+ chars; case-insensitive. Allowlist: lines containing `password_hash` or `password_salt`. The scanner skips itself (`tools/secrets_scan.py`). It reads tracked files only. | read the file |
| F1.3 | Full-history scan. What was scanned: `git log --all -p --no-color` = 184 commits, 40,735 output lines, 27,199 added (`+`) lines. Every added line was tested against the same `PATTERN` and allowlist imported from `tools/secrets_scan.py`. Result: 0 matches. Not scanned: removed lines (`-`), binary files, unreachable or dangling objects (`git fsck --lost-found`), stashes, other clones, and any secret shape not in the pattern list (for example a bare password in prose, or a key with another prefix). | one-off Python snippet (below) |
| F1.4 | File names ever added in any commit matching `.env`, `.pem`, `.key`, `secret`, `credential`: `.env.example`, `script/secrets-check`, `tools/secrets_scan.py`. No real `.env`, `.pem` or `.key` file was ever added. Command: `git log --all --diff-filter=A --name-only --format= \| grep -iE "\.env\|\.pem\|\.key\|secret\|credential" \| sort -u` | command shown |
| F1.5 | `.env` is ignored: `git check-ignore -v .env` prints `.gitignore:19:.env  .env`. `git ls-files \| grep -i env` lists only `.env.example`. | commands shown |
| F1.6 | `.env.example` content: variables `DB_PATH`, `OLLAMA_ENABLED=0`, `OLLAMA_URL=http://127.0.0.1:11434`, `OLLAMA_MODEL=qwen3:1.7b`, `OLLAMA_SMALLER_MODEL=` (empty), `OLLAMA_TIMEOUT=60`. No token, key or password value in it. | `cat .env.example` |
| F1.7 | The seed account has `password_hash = 'not-a-real-hash'`, `password_salt = 'not-a-real-salt'` (`seed/iteration-1.sql:45-48`). The schema has the columns (`migrations/0001-initial.sql:22-30`) but no code reads them (no login exists; see section 3). | `grep -rn password_hash src` |
| F1.8 | `BANNER_SIGNER` (the key that signs dispatcher-console banners): taken from `app.config`, else env `BANNER_SIGNER`, else `os.urandom(32).hex()` at each start (`src/web_ui/app.py:201`). It is not in `.env.example`. | read the line |
| F1.9 | CI (`.github/workflows/ci.yml`) installs `requirements.txt` (line 24); a grep for `audit` and `pip-audit` in the workflow found no match. Whether `script/secrets-check` runs in CI: not checked here; `grep -n secrets .github/workflows/ci.yml` will say. | `grep -n "audit\|secrets" .github/workflows/ci.yml` |

History-scan snippet (run with `$PY -`, from the repo root):

```
import subprocess,sys; sys.path.insert(0,'tools'); import secrets_scan as s
p=subprocess.run(["git","log","--all","-p","--no-color"],capture_output=True,text=True,encoding="utf-8",errors="replace")
n=sum(1 for l in p.stdout.splitlines() if l.startswith('+') and not l.startswith('+++') and s.PATTERN.search(l) and not any(a in l for a in s.ALLOWLIST))
print(n)   # printed 0
```

---

## 2. Input handling

### Routes (method, input, validation)

Every route handler opens its own SQLite connection (`connect()`), and all SQL in the routes read uses `?` placeholders (bound parameters). The only f-string SQL in `src/` is `src/purge/job.py:92` (`DELETE FROM {table} WHERE {where}`; table names and clauses come from a fixed list in the same file, the value is bound as `:cutoff`). Re-run: `grep -rn 'execute(f' src`.

| ID | Route | Method | Input | Validation (file:line) |
|---|---|---|---|---|
| F2.1 | `/healthz` | GET | none | none needed; runs `SELECT 1` (`app.py:214-221`) |
| F2.2 | `/reports` | GET | none | none (`app.py:223-232`) renders `reports.html` |
| F2.3 | `/units` | GET | none | none (`app.py:234-241`) |
| F2.4 | `/reports` | POST | JSON object or form fields: `location`, `severity_raw`, `timestamp_reported`, `reporting_unit` (required), `description` (optional) | `app.py:248`: `request.get_json(silent=True) or request.form`. `src/intake_gateway/service.py:47-62`: body must be a `Mapping` (else `InvalidBody`, 400); each required field must be a non-blank `str` (missing/empty -> `FIELD_MISSING`, wrong type or whitespace-only -> `FIELD_INVALID`); `description` must be `str` if present; `timestamp_reported` parsed by `datetime.fromisoformat` (`service.py:34-44`), bad -> 400 `INVALID_TIMESTAMP`, no offset is taken as UTC. No length limit, no future-date limit. Errors map to 400 at `app.py:256-275`. Client cannot set status or id (`test_a_client_cannot_choose_its_own_status_or_id`, `tests/integration/test_data_families_http.py:178`). |
| F2.5 | `/connectivity` | GET | none | `app.py:279-286` |
| F2.6 | `/connectivity` | POST | JSON `{"connected": bool}` | `app.py:288-315`: `json_object()` (`app.py:64-67`, non-object body -> `{}`), then `isinstance(..., bool)` else 400 `INVALID_FLAG`. Setting `true` drains the offline queue. The flag is a module global (`src/intake_gateway/queue.py:19-28`), shared by every caller. |
| F2.7 | `/proposals/pending` | GET | none | `app.py:317-323` |
| F2.8 | `/proposals/<int:id>/decision` | POST | JSON `decision`, optional `modified_unit_id` | `app.py:325-352`. Value checks in `src/decide_proposal/service.py` (decision must be one of approve/modify/reject; `modified_unit_id` must be `type(...) is int`, lines ~178-182). Error code -> status map `app.py:340-346` (404, 400, 403, else 500); `RegistryError` -> 409. |
| F2.9 | `/assignments/<int:id>/override` | POST | JSON `new_unit_id`, `reason` | `app.py:354-380`; reason required (400), 404 not found, 403 not dispatcher, `RegistryError` 409, `DecideError` -> 500. |
| F2.10 | `/overrides/<int:id>/follow-up` | POST | JSON `text` | `app.py:382-395`; `add_follow_up` requires non-blank text (`src/override_assignment/service.py:117-118`). `DecideError` -> 500. |
| F2.11 | `/reconciliations/<int:report_id>/override` | POST | JSON `version_id` (int, not bool), `reason` | `app.py:397-416`; version_id type check at `app.py:402-405`; 400/403/404 map at `app.py:410`. |
| F2.12 | `/nodes/<int:id>/heartbeat` | POST | none (path only) | `app.py:418-427`; unknown node -> 404. Unauthenticated; any caller can mark any node alive. |
| F2.13 | `/nodes/<int:id>/confirm-recovery` | POST | none | `app.py:429-442`; 403/409/404 map at `app.py:436`. |
| F2.14 | `/alerts` | GET | none | `app.py:444-455`; returns every `node_alerts` row and its `node_notices` as JSON. |
| F2.15 | `/dispatcher` | GET | query `n` (banner token) | `src/web_ui/dispatcher.py:91-126`; `n` is verified with a signed, time-limited token (`dispatcher.py:82-88`, max age 120 s, `MAX_NOTICE` 300 characters). A bad or missing token shows no banner. |
| F2.16 | `/dispatcher/proposals/<int:id>/<action>` | POST | form `modified_unit_id` (modify only); `action` in path | `dispatcher.py:129-154`; action not in approve/modify/reject -> `abort(404)`; `_whole_number` (`dispatcher.py:62-64`) accepts only `str.isdigit()` text. Success and error both answer 303 to `/dispatcher?n=<signed token>`. |
| F2.17 | `/dispatcher/assignments/<int:id>/override` | POST | form `new_unit_id`, `reason` | `dispatcher.py:157-172` |
| F2.18 | `/dispatcher/nodes/<int:id>/confirm-recovery` | POST | none | `dispatcher.py:175-184` |

Route list re-run: `grep -nE "@(app|bp)\.(get|post)" src/web_ui/app.py src/web_ui/dispatcher.py` (18 handlers; no PUT/DELETE/PATCH). Static files: Flask's default `/static/` route exists; `src/web_ui/` has no `static` folder (`ls src/web_ui` shows only `templates`).

### Request size limits

| ID | Observation |
|---|---|
| F2.19 | None configured: `MAX_CONTENT_LENGTH` is `None` (printed by `app.config.get("MAX_CONTENT_LENGTH")`), and no code in `src/web_ui/` sets it. A 5 MB non-JSON body POSTed to `/reports` was answered `400` (not rejected for size; parsed and refused for content). Flask/Werkzeug defaults for form-data memory limits apply (not set by this repo). Related: DEF-019 (no length limit on text fields; 100,000-character location accepted and stored). |
| F2.20 | `app.py:248` uses `get_json(silent=True) or request.form`: an empty JSON object `{}` is falsy, so it falls through to `request.form` (an empty form) and then fails as `FIELD_MISSING`. Not a vulnerability by itself; recorded because of the `or`. |
| F2.21 | `get_json(silent=True)` without `force=True` parses only when the request `Content-Type` is a JSON type; otherwise it returns `None`. So a JSON route called with a form or `text/plain` body sees an empty body (`json_object()` -> `{}`). `POST /reports` additionally accepts form-encoded bodies by design (`app.py:248`). Re-run: `curl -X POST -d "decision=approve" localhost:8080/proposals/1/decision` should answer 400 `INVALID_DECISION`. (Not run against a live server; derived from code and the test client.) |

### Hostile-data tests

| ID | Observation | How to re-run |
|---|---|---|
| F2.22 | `tests/data/hostile.json` (generated by `tests/data/generate.py`, fixed seed 20261105) holds synthetic entries including: SQL injection in `location` and `severity_raw`, `<script>` tag, HTML entities, emoji, right-to-left text, combining characters, whitespace-only values, number/boolean/list/object where text belongs, deeply nested values, 10k- and 100k-character text, a 2099 timestamp, a JSON list and a JSON string as the whole body. Every entry has `synthetic: true` and an `expect` field. | `$PY -c "import json;d=json.load(open('tests/data/hostile.json'));print(len(d),sorted({e['name'] for e in d}))"` |
| F2.23 | `tests/integration/test_data_families_http.py` tests: `test_hostile_input_never_crashes_the_server` (line 148), `test_hostile_input_the_specification_rejects_is_rejected` (160), `test_hostile_text_that_is_accepted_is_stored_exactly_as_sent` (168), `test_a_client_cannot_choose_its_own_status_or_id` (178), `test_the_data_contains_no_real_personal_data` (100). | `$PY -m pytest tests/integration/test_data_families_http.py -q` (not run for this sheet; the instructions were not to run the suite) |
| F2.24 | Console banner tests: `test_a_banner_forged_in_the_address_is_not_shown` (`tests/integration/test_dispatcher_ui_http.py:162`), `test_a_real_banner_is_signed_expires_and_is_shown_as_text_only` (175). Non-object-body test for JSON routes: `test_json_routes_survive_a_body_that_is_not_an_object` (same file). |
| F2.25 | Templates: `src/web_ui/templates/*.html`. Only `|safe` uses found: `reports.html:21-22` on the literal `"&mdash;"` string (not user data). `grep -rn "safe\|Markup\|autoescape" src/web_ui/templates`. The `<script>` grep in templates found none. |

### Known defects (from `docs/defect-log.md`, quoted facts)

| ID | Defect | Status in log |
|---|---|---|
| DEF-009 | JSON list/string body crashed intake with HTTP 500 | Fixed `4f4a5cc` |
| DEF-010 | list/object where text belongs crashed intake with 500 | Fixed `4f4a5cc` |
| DEF-011 | whitespace-only text accepted | Fixed `4f4a5cc` |
| DEF-012 | number/boolean accepted as text | Fixed `4f4a5cc` |
| DEF-019 | no length limit on text fields | Will not fix (log: S4/P4) |
| DEF-023 | JSON list/number body crashed four more routes with 500 | Fixed `6c470be` |
| DEF-020 | 2099 timestamp accepted | Open (log: S4/P3) |

Severity/priority labels above are those already written in the log; nothing was reassessed here.

---

## 3. Authentication

| ID | Observation | Where / re-run |
|---|---|---|
| F3.1 | No login, session, cookie, token or credential check exists in `src/`. `grep -rniE "session\|set_cookie\|login\|Authorization" src --include=*.py` (code lines) finds none outside comments and docstrings. | grep |
| F3.2 | Every acting route identifies "the dispatcher" by calling `stub_dispatcher_id(conn)`: `SELECT id FROM dispatcher_accounts WHERE role = 'dispatcher' AND is_fictional_test_account = 1 ORDER BY id LIMIT 1` (`src/decide_proposal/service.py:119-129`). Callers: `app.py:336, 365, 387, 408, 434`; `dispatcher.py:140, 166, 179`. The caller cannot name an account (docstrings at `app.py:327-328, 356`). If no such row exists the call raises `STUB_DISPATCHER_MISSING` (an unmapped `DecideError`, 500 in `app.py:346`). | read |
| F3.3 | DEF-018 (log text): "Anyone who can reach the server can approve or override; there is no login." Status Open, severity S2, priority P2, workaround "bind to localhost only", test `tests/acceptance/test_acceptance_criteria.py::test_FR_AUTH_01_AC2_an_unauthenticated_caller_cannot_approve` (strict xfail). | `docs/defect-log.md` |
| F3.4 | Routes reachable with no credentials: all 18 (section 2). That includes the state-changing ones: `POST /reports`, `/connectivity`, `/proposals/<id>/decision`, `/assignments/<id>/override`, `/overrides/<id>/follow-up`, `/reconciliations/<id>/override`, `/nodes/<id>/heartbeat`, `/nodes/<id>/confirm-recovery`, and the three `/dispatcher/...` POSTs. Demonstrated with the Flask test client on a temp seeded DB (not the dev DB): `POST /proposals/1/decision {"decision":"approve"}` with no credentials and an `Origin: http://evil.example` header returned 200 with `final_status: approved`, `decided_by: '1'`, and created a notification row. | test-client run (below) |
| F3.5 | Bind address: `script/start` runs `python -m flask --app src.web_ui.app run --host 127.0.0.1 --port 8080`; `src/web_ui/app.py:463` (`__main__`) uses `app.run(host="127.0.0.1", port=8080)`. Nothing in the repo reads a host or port from the environment. A user can still pass `--host` to `flask run` by hand. | read |
| F3.6 | The `username` column is `demo-dispatcher`, hash/salt are placeholder strings (`seed/iteration-1.sql:45-48`). The `dispatcher_accounts` table has roles `admin`, `dispatcher`, `observer` (`migrations/0001-initial.sql:27`). | read |
| F3.7 | No Flask session signing setting is configured (the app does not use `session`). The `BANNER_SIGNER` is a separate key (F1.8). | read |

---

## 4. Authorization

The check is "role of the account whose id was passed in is `dispatcher` or `admin`". Because the account passed in is always the stub (F3.2), a refusal occurs only if the database row for the stub is changed (that is how the tests produce it).

| ID | Action | Role check (file:line) | Allowed roles | Refusal | Tests |
|---|---|---|---|---|---|
| F4.1 | Decide proposal (approve/modify/reject), JSON and console | `src/decide_proposal/service.py:185-189` | dispatcher, admin | `DecideError NOT_A_DISPATCHER`; JSON route 403 (`app.py:345`); console route: 303 redirect with banner "Proposal N was not changed ... (NOT_A_DISPATCHER)" (`dispatcher.py:67-69, 143-144`) | `tests/unit/test_human_decision.py:164 test_observer_account_is_refused`; `tests/unit/test_human_modify.py:116` |
| F4.2 | Override an assignment | `src/override_assignment/service.py:32-36` (`_check_dispatcher`) | dispatcher, admin | `OverrideError NOT_A_DISPATCHER`; JSON 403 (`app.py:371`); console as above | `tests/unit/test_override_assignment.py:169` |
| F4.3 | Add override follow-up | `src/override_assignment/service.py:116` (same `_check_dispatcher`) | dispatcher, admin | `OverrideError NOT_A_DISPATCHER`; JSON route maps non-404 `OverrideError` to 400 (`app.py:389`), not 403 | not found by name in `tests/` (`grep -rn "follow_up" tests/unit/test_override_assignment.py` to check whether the observer case is covered) |
| F4.4 | Override a reconciliation | `src/negotiation/reconcile.py:100-102` | dispatcher, admin | `ReconcileError NOT_A_DISPATCHER`; 403 (`app.py:410`) | `tests/unit/test_reconcile.py:127` |
| F4.5 | Confirm a node's recovery | `src/heartbeat/service.py:120-122` | dispatcher, admin | `HeartbeatError NOT_A_DISPATCHER`; 403 (`app.py:436`); console banner | `tests/unit/test_heartbeat.py:157` |
| F4.6 | Submit report, connectivity toggle, node heartbeat, all GETs | no role check in code | n/a (anyone) | n/a | n/a |
| F4.7 | The `observer` role | exists in the schema CHECK (`migrations/0001-initial.sql:27`); the only effect in code is exclusion from the checks above. No read-only observer view or separate observer routes exist. | | | |
| F4.8 | "admin" | treated identically to dispatcher in all five checks; no admin-only action found (`grep -rn "'admin'" src`). | | | |
| F4.9 | Acceptance coverage for FR-AUTH-01: see `docs/traceability.csv` rows `FR-AUTH-01-*` and `docs/test-plan.md:23` (login "Not built"). | | | | `grep FR-AUTH docs/traceability.csv` |
| F4.10 | Nothing in the code ties the recorded `decided_by`/`dispatcher_account_id` to a real person; the stored id is the stub's (F3.4 showed `decided_by: '1'`). | | | | |

---

## 5. Transport

| ID | Observation | Where / re-run |
|---|---|---|
| F5.1 | Plain HTTP only. No TLS configuration, certificate, `ssl_context`, or HTTPS redirect in `src/` or `script/`. The Ollama client refuses anything but `http://` to loopback (`ollama_client.py:66-70`; `https://127.0.0.1:11434` is a listed refusal in the unit test named in `docs/change-requests/CR-013-https-transport.md`). `CR-013` (draft, Ben's) discusses the HTTPS change; it is not implemented. | grep |
| F5.2 | Bind address 127.0.0.1:8080 (F3.5). | |
| F5.3 | CSRF: no CSRF token, header check, `Origin`/`Referer` check or SameSite cookie anywhere (no cookies exist). `dispatcher.py:9-11` says so in its docstring: "these forms carry no login and no CSRF token; both arrive with sign-in". `grep -rni csrf src` finds only that docstring. Demonstrated with the test client: `POST /dispatcher/proposals/9999/approve` with header `Origin: http://evil.example` -> 303 redirect (processed, not refused); `POST /proposals/1/decision` JSON with the same header -> 200 and approved (F3.4). A plain HTML form on another site can submit `application/x-www-form-urlencoded` to the `/dispatcher/...` POSTs and to `POST /reports`; the JSON routes need a JSON `Content-Type` (F2.21), which a cross-site HTML form cannot set without a CORS preflight; no CORS headers are sent, so a preflight from another origin would not be approved by a header from this server. (Browser behavior described from the standard, not tested here.) | test client |
| F5.4 | Security headers actually sent. Test-client results (temp seeded DB, `app.test_client()`): `GET /healthz`: `Content-Type: application/json`, `Content-Length` only. `GET /dispatcher`: `Content-Type: text/html; charset=utf-8`, `Content-Length` only. `GET /reports` and `POST /reports`: same pattern. Not sent: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`, `Cache-Control`. No `after_request` handler exists (`grep -n after_request src` finds none). No server was started for this check (the test client calls the WSGI app directly; no port was opened). A real `flask run` also adds `Server: Werkzeug/...` and `Date`. | snippet below |
| F5.5 | Signed banner token: `src/web_ui/dispatcher.py:72-88`. `URLSafeTimedSerializer(BANNER_SIGNER, salt="dispatcher-banner")`; payload `{"m": message[:300], "ok": bool}`; `loads(token, max_age=120)`; failures (`BadSignature`, `KeyError`, `TypeError`) show no banner. The token is carried in the URL query `n` of a 303 redirect (so it appears in the browser address bar/history and in the Werkzeug request log). The signing key is random per process start unless `BANNER_SIGNER` is set (F1.8), so tokens do not survive a restart. The token is signed, not encrypted: itsdangerous payloads are base64 and readable by anyone holding the URL (message text is system-written, e.g. "Proposal 7 approved; unit 3 notified."). The template renders `notice` through normal autoescape (F2.25). `SignatureExpired` is a subclass of `BadSignature`, which is the case covered by the `except`. | read; tests at `tests/integration/test_dispatcher_ui_http.py:162,175` |
| F5.6 | Debug mode: `app.debug` was `False` in the run above. No `debug=True` in `src/`; `script/start` does not set `FLASK_DEBUG`; `.env.example` has no debug variable. `flask run` enables the debugger/reloader only if `--debug` or `FLASK_DEBUG=1` is supplied by the operator. | grep |

Header and CSRF probe (run from the repo root; uses a temp DB, not `data/dev.sqlite`):

```
$PY - <<'EOF'
import os,tempfile,subprocess,sqlite3
d=tempfile.mkdtemp(); os.environ["DB_PATH"]=os.path.join(d,"t.sqlite")
subprocess.run(["./.venv/Scripts/python","tools/migrate.py",os.environ["DB_PATH"]],check=True)
c=sqlite3.connect(os.environ["DB_PATH"]); c.executescript(open("seed/iteration-1.sql",encoding="utf-8").read()); c.commit()
from src.web_ui.app import app
cl=app.test_client()
r=cl.get("/dispatcher"); print(r.status_code, dict(r.headers))
r=cl.post("/proposals/1/decision",json={"decision":"approve"},headers={"Origin":"http://evil.example"}); print(r.status_code, r.get_json())
EOF
```

Options with costs (only where relevant to Ben's decision; none is recommended here):
- Response headers: one `@app.after_request` function (about 6 lines); cost is a small test and possible interaction with the console's own pages (none loads external assets: `grep -rn "http" src/web_ui/templates` found no external URLs).
- CSRF/Origin check: a `before_request` rejecting non-GET requests whose `Origin` is present and not `http://127.0.0.1:8080`/`localhost:8080` is a few lines plus tests; it does not substitute for login, and a client that sends no `Origin` (curl, the test client) is unaffected. A signed per-form token needs a session or a signed-in identity, which FR-AUTH-01 provides later.
- HTTPS: see `CR-013` (cost listed there: a certificate, the start command, one function and its tests).

---

## 6. Dependencies

Commands run (pip-audit 2.10.1 installed into the venv with `./.venv/Scripts/python -m pip install pip-audit`; the network was reachable, the tool returned results):

```
$ ./.venv/Scripts/pip-audit -r requirements.txt
No known vulnerabilities found

$ ./.venv/Scripts/pip-audit            # audits everything installed in the venv
Found 9 known vulnerabilities in 1 package
Name       Version ID                  Fix Versions
setuptools 65.5.0  PYSEC-2022-43012    65.5.1
setuptools 65.5.0  PYSEC-2022-43012    65.5.1
setuptools 65.5.0  PYSEC-2025-49       78.1.1
setuptools 65.5.0  PYSEC-2025-49       78.1.1
setuptools 65.5.0  PYSEC-2026-1918     70.0.0
setuptools 65.5.0  PYSEC-2026-1918     70.0.0
setuptools 65.5.0  PYSEC-2026-3447     83.0.0
setuptools 65.5.0  PYSEC-2026-3447     83.0.0
setuptools 65.5.0  GHSA-xmj3-9gf7-h52w 84.1.0
```

| ID | Observation |
|---|---|
| F6.1 | `pip-audit -r requirements.txt` (16 pinned packages: blinker, click, coverage, Flask 3.1.3, hypothesis, iniconfig, itsdangerous, Jinja2, MarkupSafe, packaging, pluggy, pytest-cov, pytest, ruff, sortedcontainers, Werkzeug 3.1.9): `No known vulnerabilities found`. The JSON form of the same command also listed each dependency with `"vulns": []`. This is the list CI installs (`ci.yml:24`). |
| F6.2 | The venv audit found 5 distinct advisory IDs (9 rows, each shown twice for four of them) against one package, `setuptools 65.5.0`, which is not in `requirements.txt`. Where it comes from: it is present in this venv only (installed by the venv bootstrap; pip is 26.2.2, Python 3.11). A fresh CI install from `requirements.txt` does not name it; whether a CI runner has its own `setuptools` was not checked. |
| F6.3 | Advisory table (IDs from the pip-audit output; the descriptions are NOT pulled from the output, which does not print them. Ben: open each link and read the advisory yourself before writing anything). |

| Advisory ID | Package | Installed | Fixed in | Link |
|---|---|---|---|---|
| PYSEC-2022-43012 | setuptools | 65.5.0 | 65.5.1 | https://osv.dev/PYSEC-2022-43012 |
| PYSEC-2025-49 | setuptools | 65.5.0 | 78.1.1 | https://osv.dev/PYSEC-2025-49 |
| PYSEC-2026-1918 | setuptools | 65.5.0 | 70.0.0 | https://osv.dev/PYSEC-2026-1918 |
| PYSEC-2026-3447 | setuptools | 65.5.0 | 83.0.0 | https://osv.dev/PYSEC-2026-3447 |
| GHSA-xmj3-9gf7-h52w | setuptools | 65.5.0 | 84.1.0 | https://osv.dev/GHSA-xmj3-9gf7-h52w (also https://github.com/advisories/GHSA-xmj3-9gf7-h52w) |

Code-path notes (grep evidence, no reachability judgement; Ben verifies IDs and makes that call):
- `grep -rnE "setuptools|pkg_resources" --include=*.py --include=*.txt --include=*.sh --include=*.yml .` (venv excluded) returned no match: no file in the repo imports or names `setuptools`.
- Third-party packages imported by `src/` and `tools/`: `flask` (`app.py`, `dispatcher.py`) and `itsdangerous` (`dispatcher.py:22`). All other `src` imports are standard library or project modules.
- The five IDs were reported by pip-audit's vulnerability sources; they were not independently re-fetched from osv.dev or github.com/advisories by this sheet. The pip-audit "Fix Versions" column is the only version information included.
- Not done: `pip-audit` against a second index/service; license check; an SBOM; pinning of transitive hashes (`requirements.txt` has pins, not hashes).

Re-run: `./.venv/Scripts/pip-audit -r requirements.txt` and `./.venv/Scripts/pip-audit`.

---

## 7. Logging

### What is recorded, and where

| ID | Store | Columns of note | Append-only enforcement | Purged at 24 h? |
|---|---|---|---|---|
| F7.1 | `dispatcher_overrides` | assignment id, dispatcher id, reason (free text typed by the dispatcher), `overridden_at` | trigger `dispatcher_overrides_no_edit` (`migrations/0003-override-follow-ups.sql:28`); delete is not blocked (purge deletes) | yes (`purge/job.py`: `dispatcher_overrides`) |
| F7.2 | `override_follow_ups` | override id, dispatcher id, `text` (free text), `added_at` | trigger `override_follow_ups_no_edit` (0003:22) | yes |
| F7.3 | `tiebreak_log` | winner/loser proposal ids, `resolved_at` | trigger `tiebreak_log_no_edit` (`migrations/0006...:30`) | yes |
| F7.4 | `reconciliation_log` | report id, original/chosen version ids, `decided_at` (and a reason column per the review's code; check the migration) | trigger `reconciliation_log_no_edit` (`migrations/0007...:49`) | yes |
| F7.5 | `node_alerts`, `node_notices` | node id, text such as "Node N (role) has not responded for S seconds." (`src/heartbeat/service.py:102`), `confirmed_at` | no trigger found for these two in the migrations list (`grep -n TRIGGER migrations/*.sql`) | NOT in the purge list (`src/purge/job.py` header: agent nodes "hold no incident data and are left alone"; `node_alerts` and `node_notices` are not named in `steps`) |
| F7.6 | `unit_events`, `agent_inboxes` | unit id, status, proposal id, timestamps (`migrations/0008...:26-33`) | not checked for a trigger | yes (`EXPIRED_EVENTS`) |
| F7.7 | `agent_proposals` | `reasoning`, `input_data` (the report text the agent saw, DEF-014 fix, trigger `agent_proposals_input_data_is_final` in 0004), `model_identifier` | trigger for `input_data` | yes |
| F7.8 | `incident_reports`, `incident_versions` | `location`, `severity_raw`, `description`, `reporting_unit`, timestamps | `incident_versions_data_is_final` trigger | yes |
| F7.9 | `notifications` | assignment id, unit id, `sent_at` (a row, not a message; DEF-017) | | yes |
| F7.10 | `human_escalations` | report id, reason, timestamps | | yes |

### Process output (stderr/stdout)

| ID | Observation |
|---|---|
| F7.11 | Application `print(..., file=sys.stderr)` calls in `src/`: `app.py:174` (`reservation sweeper error: {exc}`), `app.py:193` (`node watcher error: {exc}`), `chain.py:109` (bad `OLLAMA_TIMEOUT` value echoed with `!r`), `chain.py:132` (`model integration not used: {exc}`, which includes the rejected URL). No `logging` module use in `src/` (`grep -rn "logging" src`). None of these prints include report text. `{exc}` for a `sqlite3.Error` can contain SQL error text; not tested for report content. |
| F7.12 | The Werkzeug development server logs one stderr line per request: method, path with query string, status. For the console this includes `GET /dispatcher?n=<signed token>`. POST bodies are not logged by Werkzeug. |
| F7.13 | Personal data: the intake form has no name or phone field (`REQUIRED_FIELDS`, `intake_gateway/service.py:12`); `description` and `severity_raw` are free text and can contain whatever a reporter types. `reporting_unit` is a free-text string. The Ollama client sends location, report text, description and time, "not who sent it" (`ollama_client.py` docstring; `_prompt` at ~line 81 uses those four fields). `tests/integration/test_privacy_http.py` posts a report with extra fields `caller_name`, `caller_phone` and `caller` (`CALLER_NAME`, `CALLER_PHONE`, lines 12-13; body built at line 56) and checks the purge removes it; intake ignores unknown fields (the INSERT at `service.py:~66` names only the five known columns). Acceptance test `test_NFR_PRIV_01_AC1_...` (`tests/acceptance/test_acceptance_criteria.py:516`). Whether free-text personal data reaches any log other than the tables above: stderr prints (F7.11) do not carry it; `node_alerts` text (F7.5) is system-written. |
| F7.14 | Where a stack trace could reach a user: no `errorhandler` registered (`grep -rn errorhandler src` finds none), so an unhandled exception yields Flask's default `500 Internal Server Error` HTML page, and with `debug` off (F5.6) the page does not include the traceback; the traceback goes to stderr. Unmapped `DecideError` codes are returned as JSON with the exception's own message and status 500 (`app.py:346-347`, `375`, `392`); `RegistryError` messages are returned as JSON (`app.py:349, 377`). `UNIT_LOST_BEFORE_APPROVAL` responses include `Underlying: {exc.cause}` text (`app.py:125-131`). `STUB_DISPATCHER_MISSING` returns a message naming the seed file. |

### 24-hour purge (`src/purge/job.py`)

| ID | Observation |
|---|---|
| F7.15 | `purge(conn, now=None, retention_hours=24)` hard-deletes, in one transaction, rows past the cutoff and rows whose parent is being deleted, in foreign-key order (`job.py:63-113`). Rolls back and raises `PurgeFailed` on `sqlite3.Error`. Resets (does not delete) units held by purged proposals. Never touches `dispatcher_accounts`, `scenario_runs`, `agent_nodes` (docstring). |
| F7.16 | What triggers it: `tools/purge.py` (command-line). A grep for callers found `src/negotiation/reconcile.py`, `src/purge/job.py`, `tools/purge.py`, `tools/write_test_results.py` (the `reconcile.py` hit is a comment, line 6: "only the 24-hour purge removes them"). No scheduler, no thread and no `script/start` line invokes the purge (`grep -rn purge script src/web_ui`). So the 24 hours is enforced only when somebody runs `tools/purge.py`. |
| F7.17 | Tables not in the purge `steps`: `node_alerts`, `node_notices`, `dispatcher_accounts`, `scenario_runs`, `units`, `agent_nodes`. |
| F7.18 | SQLite deletes do not zero the freed pages; the database file, any `-wal`/`-journal` file and any backup retain old bytes until reused or `VACUUM`ed. `grep -rn "VACUUM" src tools` to check whether the repo ever vacuums. Not tested here. |
| F7.19 | The database file is `data/dev.sqlite` by default (`src/db.py:10`, overridable with `DB_PATH`); `data/` is in the repo tree (check `git check-ignore -v data/dev.sqlite`). |

---

## 8. Model integration facts (new this week)

Source: `src/classify_propose/ollama_client.py`, `src/classify_propose/chain.py`, `src/decide_proposal/service.py`, `docs/defect-log.md`.

| ID | Observation | Where |
|---|---|---|
| F8.1 | Loopback-only rule: the base URL must have scheme `http` and hostname in `{127.0.0.1, localhost, ::1}`; otherwise `OllamaModel.__init__` raises `ValueError`. `https://` is refused. The check is on the host string; `localhost` is resolved by the operating system when the request is made (the check does not look at the resolved address). | `ollama_client.py:49, 66-70, 99-104` |
| F8.2 | No redirects: `_NoRedirects.redirect_request` returns `None`; a 3xx surfaces as `HTTPError` and raises `OllamaBadResponse("... redirects are refused")`. | `ollama_client.py:62-64, 124-125` |
| F8.3 | No proxy: opener built with `ProxyHandler({})`. | `ollama_client.py:65` |
| F8.4 | 1 MB cap: `response.read(MAX_RESPONSE_BYTES + 1)`, then `len(raw) > 1 MiB` raises `OllamaBadResponse`. The read stops at 1 MiB + 1 bytes, so an oversized body is not fully downloaded. | `ollama_client.py:47, 119, 133-134` |
| F8.5 | 60 s cap: `timeout=self.timeout` passed to `urlopen` (default 60.0; `OLLAMA_TIMEOUT` env, a non-positive or non-numeric value falls back to 60 with a stderr message). `urllib`'s `timeout` is a per-socket-operation limit, not a total deadline: a server that sends bytes slowly enough to keep each read under the limit could take longer than 60 s in total. Not tested by this sheet; `tests/integration/test_ollama_chaos_http.py` and `tests/unit/test_ollama_client.py` cover timeouts against stub servers (check whether a slow-drip case exists: `grep -n "slow\|drip" tests/unit/test_ollama_client.py tests/integration/test_ollama_chaos_http.py`). Evidence file: `docs/evidence/m12-outage-2x0.05min.json`. | `ollama_client.py:46, 118; chain.py:99-111` |
| F8.6 | Kill switch: the model tier is used only when env `OLLAMA_ENABLED == "1"`; unset or any other value (including `true`) means rules tier only. `build_chain()` reads the environment on every call (every report), so flipping it needs no restart in the same process; `.env.example` sets it to `0`. | `chain.py:114-135`; `.env.example` |
| F8.7 | If `OLLAMA_URL` is non-loopback, `build_chain` prints `model integration not used: ...` to stderr and continues with the rules tier only (no exception to the caller). | `chain.py:131-133` |
| F8.8 | What is sent to the model: location, `severity_raw` ("report"), optional `description`, `timestamp_reported`; not `reporting_unit`. The response parse removes `<think>...</think>`, requires a JSON object with `severity`, `unit_type`, `confidence`, `reasoning`, and passes through the same `_validate` as the rules model (DEF-015 fix). One retry restates the schema; after that `OllamaBadResponse`. The model's earlier reply (first 2000 characters) is placed back into the retry prompt. Report text is placed in the prompt unescaped after fixed labels (a report can contain text addressed to the model; prompt-injection behavior was not tested here). | `ollama_client.py:79-84, 140-170` |
| F8.9 | DEF-029 (`docs/defect-log.md` line ~274): a real model (`qwen3:1.7b`, Ollama 0.40.15, run 2026-11-11) scored a barely informative report Serious/Shelter at confidence 75, exactly the auto-dispatch threshold, so the safety rule allowed dispatch with no human review; the fake rules model scored the same text 40. Log status: Fixed `b7030ae`; fix: answers from a real model need confidence at or above `MODEL_AUTO_APPROVE_MIN` (default 85, "never below 75"; a bad or too-low value falls back to 85); the rules tier keeps 75. The log says 85 is a provisional number chosen by the assistant and Ben is to confirm or change it. Regression test: `test_decide_auto_holds_a_real_model_proposal_at_75_but_approves_a_rules_proposal_at_75`. | `src/decide_proposal/service.py:15-40`; log |
| F8.10 | The tier order and fallback are in `chain.py` (`ModelChain`, `ChainExhausted`); the rules tier is always last, so a model failure falls back rather than blocking intake (`app.py:105-110` handles `ClassifyError`). |

---

## Things stated as fact that a reader may want to look at first (not verdicts)

1. `src/web_ui/app.py:325-352` and 7 other POST handlers act as the stub dispatcher for any caller; demonstrated 200 approve with a foreign `Origin` header (F3.4, F5.3).
2. `src/web_ui/app.py:418-427`: `POST /nodes/<id>/heartbeat` has no caller check of any kind (F2.12).
3. `src/purge/job.py` is not called by `script/start`, `src/web_ui/` or any thread; only `tools/purge.py` runs it (F7.16). `node_alerts` and `node_notices` are outside it (F7.5).
4. No security response headers and no `MAX_CONTENT_LENGTH` (F5.4, F2.19).
5. `pip-audit -r requirements.txt` clean; `pip-audit` of the venv reports setuptools 65.5.0 (F6.1-F6.3).
6. `DEF-029` fix threshold 85 was set by the assistant, not Ben (F8.9).

## Update 2026-11-18: dependency audit in CI

`.github/workflows/ci.yml` now has an `audit` job (own hash-pinned tool set in `requirements-audit.txt`) that runs `python -m pip_audit --require-hashes --disable-pip -r requirements-dev.txt` on every push, every pull request to `main` and weekly (Mondays 06:17 UTC). Run locally on 2026-11-18: "No known vulnerabilities found" for `requirements.txt` and for `requirements-dev.txt`. This supersedes F1.9 above (no audit in CI).
