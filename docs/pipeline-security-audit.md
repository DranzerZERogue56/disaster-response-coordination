# CI pipeline and shell-script audit (2026-11-18)

Facts come from reading `.github/workflows/ci.yml` and `script/*` and from the tests in `tests/unit/test_pipeline_and_script_hygiene.py`. `shellcheck` is not installed here, so the scripts were read by hand and parsed with `bash -n`. **Recommendation** marks my opinion.

## GitHub Actions

| Concern | Finding |
|---|---|
| Script injection through untrusted contexts | None. No `run:` step interpolates a `${{ }}` value (branch names, PR titles, issue text, step outputs). A test fails the build if one appears. |
| Unpinned third-party actions | None. `actions/checkout` and `actions/setup-python` are pinned to full commit hashes (since 2026-11-18); a test enforces 40-character hashes. Both are GitHub's own actions. Dependabot (new `.github/dependabot.yml`) proposes updates as pull requests, never merges them. |
| Over-permissive `GITHUB_TOKEN` | **DEF-041, fixed.** There was no `permissions:` block. Now `contents: read` at the top, which is all the job needs. Checkout no longer stores the token in `.git/config`. **Not checked:** the repository's own default-token setting (Settings > Actions > General); **Recommendation:** set it to read-only there too. |
| `pull_request_target` and `workflow_run` misuse | Neither is used; the workflow runs on `push` and on `pull_request` against `main`, so code from a fork runs with a read-only token and no secrets. A test fails the build if either trigger is added. |
| Cache poisoning | Low risk, not removed. `setup-python` caches pip downloads keyed on the hash of `requirements-dev.txt`. Pull-request caches are scoped to the pull request, and installs use `--require-hashes`, so a tampered cached wheel would fail the hash check. **Recommendation:** if you ever add a step that restores a cache and then runs it (build output, virtualenvs), key it with a hash of the inputs and do not share it with pull requests. |
| Other | A job time limit (30 minutes) now exists. No secrets, no artifacts uploaded, no self-hosted runners, no third-party marketplace actions. |

## Shell scripts (`script/*`)

| Concern | Finding |
|---|---|
| Silent failures (`set -e` omissions) | None. Every script begins with `set -euo pipefail` (unset variables and failed pipe stages also stop it). `common.sh` is only sourced. Tests enforce this on every script. |
| Unquoted variables and word splitting | None found. `$DB_PATH`, `$PYTHON`, `$PY` and `$(dirname "$0")` are always quoted; a test scans for unquoted uses. A path with spaces works. |
| Secret leakage in logs | No `set -x`, no `echo` of a secret, no CI secrets. The only secret printed is the one-time password and phone key from `tools/enrol_dispatcher.py`, once, on purpose, to the person running it (never run it in CI). |
| Secrets in process lists | No script or tool takes a password on the command line (the enrol tool takes username, role and database path only). `SESSION_SIGNER` and `BANNER_SIGNER`, if set, are environment variables and are visible to the same user's other processes; they are random per start by default. |
| Code execution | No `eval`, `curl | sh`, `sh -c` or downloads in any script (a test enforces it). |
| `seed --reset` | Deletes the file named by `$DB_PATH`. It is quoted and has a default, but it will delete whatever path the environment names. **Recommendation:** only pass paths you mean. |

## Not done

- No `actionlint` or `shellcheck` run (not installed here); no check of the GitHub repository settings (default token permissions, branch protection, required reviews); Dependabot has not run yet; CI has not run on the hash-pinned workflow because nothing has been pushed.
