# How the CI pipeline works

CI only: it builds and tests every change. Nothing is deployed or released automatically. Source of truth: `.github/workflows/ci.yml`.

```mermaid
flowchart TD
    A[Push to any branch] --> CI
    B[Pull request into main] --> CI
    C[Weekly, Mondays 06:17 UTC] --> CI
    D[Dependabot PR] --> CI

    subgraph CI [GitHub Actions: read-only token, no secrets]
        direction TB
        subgraph BUILD [build job: Python 3.11 and 3.12 in parallel]
            direction TB
            b1[Checkout, no stored token] --> b2[Install pip 26.2.2 + hash-pinned requirements-dev.txt]
            b2 --> b3[secrets-check]
            b3 --> b4[lint: Ruff incl. security rules]
            b4 --> b5[test: 815 tests, coverage gate 90%]
            b5 --> b6[build: compile + app starts]
            b6 --> b7[smoke: healthz checks]
        end
        subgraph AUDIT [audit job]
            direction TB
            a1[Checkout] --> a2[Install hash-pinned pip-audit] --> a3[pip-audit on requirements-dev.txt]
        end
    end

    CI --> R{All green?}
    R -- yes --> M[Ready: Ben tests live, then merges to main]
    R -- no --> X[Fix on the branch and push again]
```

**Text version of the diagram:** four things start CI (a push to any branch, a pull request into main, a weekly schedule, and a Dependabot pull request). CI runs two jobs side by side with a read-only token and no secrets. The build job, once for Python 3.11 and once for 3.12, checks out the code, installs hash-pinned packages, then runs secrets-check, lint, test (with the coverage gate), build and smoke in that order. The audit job installs a hash-pinned pip-audit and checks the pinned dependencies against known vulnerabilities. If everything is green the change is ready for the owner to test live and merge to main; if not, it is fixed on the branch and pushed again.

A failing step stops its job and turns the run red. There is no deploy step; submissions and tags are made by hand.
