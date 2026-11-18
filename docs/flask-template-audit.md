# Flask 3.1 / Jinja2 web-layer audit, pytest and Ruff check

Date: 2026-11-18. Scope: the three Jinja2 templates, the Flask configuration, response headers, cookies, request limits, and the test and lint tools. Method: reading the code, live probes against the real app with the test client (throwaway scripts, deleted after), and advisory pages read from OSV and the Pallets GitHub advisories (NVD would not render, so NVD records are unverified).

Facts below are things I ran or read. Items marked **Recommendation** are my opinion and are Ben's to accept.

## Pinned versions

Flask 3.1.3, Jinja2 3.1.6, Werkzeug 3.1.9, MarkupSafe 3.0.4, itsdangerous 2.2.0, pytest 9.1.1, pytest-cov 7.1.0, Ruff 0.17.2 (all hash-pinned in `requirements*.txt`).

## The three CVE ids

| Id | What it is | Affects us? |
|---|---|---|
| CVE-2026-27205 | Flask: `session` does not always add `Vary: Cookie` (for example when read with `in`). Low. Fixed in Flask 3.1.3. | No: we run 3.1.3. |
| CVE-2025-27516 | Jinja2: sandbox breakout through the `\|attr` filter reaching `str.format`. Moderate. Fixed in 3.1.6. | No: we run 3.1.6, and we do not use the sandbox, `\|attr` or render user-supplied templates. |
| CVE-2024-27516 | Does not match Flask or Jinja2: it is a template injection in the product Live Helper Chat (before 4.34v). | Not applicable. |

Other Pallets advisories since late 2024 (the Flask signing-key fallback setting, Jinja2 sandbox filename and `str.format` issues, four Werkzeug `safe_join` Windows device-name issues) are all fixed at or below the versions we pin. The Werkzeug ones matter because this runs on Windows, and `safe_join` is how Flask serves `/static/`.

## Findings by class

| Class | Result |
|---|---|
| Server-side template injection | None found. No `render_template_string`, `Template(...)`, `Markup`, `\|attr`, `\|tojson`, raw blocks or disabled autoescape. Hostile text (`{{7*7}}{{config}}`, `{% for %}`, `${7*7}`) was stored and rendered back as inert text. |
| Cross-site scripting | None found. Autoescape is on for `.html`. The only `\|safe` uses are two constant `&mdash;` strings in `reports.html`. Script tags, `<img onerror>`, `<svg onload>`, quote breakouts and `javascript:` text, sent in location, severity, unit and description, came back escaped on `/reports` and `/dispatcher`. The CSP (DEF-031) also forbids inline script. |
| CSRF | Every form on the console carries the per-session `csrf_token`, enforced when the sign-in is on (the default through `script/start`). With `AUTH_ENFORCED=0` there is no sign-in and no CSRF check; that mode is for demos and tests. `SameSite=Strict` on the session cookie is the second layer. |
| Host header / DNS rebinding | **Defect DEF-036, fixed.** Every Host value was served. A rebinding page could reach the app on 127.0.0.1 with its own name. Now `TRUSTED_HOSTS` allows `localhost` and `127.0.0.1` (any port); `ALLOWED_HOSTS` adds names for a deployment. Proxy headers (`X-Forwarded-Host`) were already ignored by default. Limit: Werkzeug cannot match IPv6 literals, so `http://[::1]:PORT/` is refused (the app does not bind `::1` anyway). |
| Resource exhaustion | **DEF-038 and DEF-039, fixed.** A 20 MB JSON body was accepted and stored; now `MAX_CONTENT_LENGTH` is 1 MiB (413) and `MAX_FORM_PARTS` is 100. The console rendered every waiting proposal (3.9 MB for 3,000); it now shows the 200 oldest with a "N more are not shown" notice. The hidden ones still time out and free their units as before. This ends the "no size cap" accepted risk in S-05; DEF-019 (no per-field length rule) stays Will not fix because no requirement sets one. |
| Cookie settings | `HttpOnly` and `SameSite=Strict` are set, the cookie is signed (readable by the browser owner, not forgeable), sessions are also tracked server side and expire. `Secure` is set only when the request is HTTPS, so it is absent on `http://127.0.0.1`, which is correct for local use. **Recommendation:** when HTTPS is added (backlog B-11), set `SESSION_COOKIE_SECURE` unconditionally and consider the `__Host-` cookie name prefix. |
| Response headers | CSP, `X-Frame-Options: DENY`, `nosniff` and `Referrer-Policy: no-referrer` were already sent (DEF-031). **DEF-037, fixed:** no `Cache-Control`; now `no-store` on everything except `/static/`. Not set, and judged not worth it for a localhost app: HSTS (needs HTTPS), `Permissions-Policy`, cross-origin isolation headers. |

## pytest

- pytest 9.1.1 with one plugin, `pytest-cov`. No third-party plugin is auto-loaded.
- Predictable temporary directories: pytest creates its base folder under the system temp directory per user. I did not change it. **Recommendation:** on a shared machine, set `--basetemp` to a folder inside the repo; I held back because the regression-proof tool runs pytest in several worktrees and a fixed base folder could collide.
- Legacy `py` package (the ReDoS one): **not installed**. The `py.py` file in site-packages is pytest's own small shim, whose comment says it steps aside if the real package exists.
- Code execution by design: pytest imports and runs `conftest.py`, test modules and plugins. So "run the tests" means "run this repository's code". Only run the suite on a checkout you trust, and review a pull request's `conftest.py` and test changes the way you review source.

## Ruff

- Before today there was no Ruff configuration, so only the default rules ran (no security rules). **Done:** `ruff.toml` now enables the flake8-bandit security rules (`S`) and bugbear (`B`), and `script/lint` also covers `tools/`.
- Result: 7 findings in `src`, all judged safe and suppressed with a stated reason (six are the purge job's SQL assembled from fixed constants with a bound parameter; one is the model client's URL open, restricted to plain http on loopback). Tests and tools have per-folder exceptions with the reason written next to each. Three trivial tool findings were fixed.
- Ruff has no direct core CVE that I checked: **not researched** in this audit. Ruff is a pinned binary wheel, hash-checked on install.
- Editor extensions and unofficial package managers: **not checked from here.** **Recommendation:** install Ruff only from PyPI through `requirements-dev.txt` (what `script/setup` does), keep any editor extension updated, and avoid third-party redistributions.

## Not done

- No live test with HTTPS; no browser-based scan (ZAP, Burp).
- No fuzzing of multipart parsing beyond the field-count probe.
- NVD records for the three ids; PyPI "newest version" checks.
