# Engineering Validation Map

| Surface | Gate | Failure blocked |
|---|---|---|
| Packaging | `make wheel-smoke` | UI assets missing from wheel, import only works through `PYTHONPATH` |
| Dependencies | `make dependency-contracts` | untracked dependency drift, missing constraints, missing security deps |
| Test architecture | `make test-architecture` | thin test suite, missing contract tests |
| Automation | `make automation-contract` | Makefile/CI/release script drift |
| Bibliography | `make bibliography` | scientific claim drift, missing source boundaries |
| API | `make api-smoke`, `pytest` | schema/auth/limit/error regressions |
| Frontend | `make frontend-quality` | unsafe dynamic HTML, missing operational UI sections |
| Dynamic environment | `make dynamic-probe` | repeated-run instability, auth bypass, storage concurrency regressions |
| Security | `make security-static`, `make dependency-audit` | static security findings, known vulnerable dependencies |
| Release evidence | `make manifest-check`, `make evidence-bundle` | untraceable or stale release artifacts |
