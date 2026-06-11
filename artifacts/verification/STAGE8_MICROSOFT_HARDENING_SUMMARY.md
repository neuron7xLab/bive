# Stage 8 Microsoft Hardening Summary

Implemented remediation from Microsoft-oriented audit:

- SDL-style STRIDE threat model with machine validator.
- Microsoft/Azure-style REST versioning: `api-version=2026-06-11` required for `/api/v1/*`.
- Microsoft-style correlation: `x-ms-request-id` propagation and `x-ms-client-request-id` echo.
- Microsoft-style error envelope: `{ "error": { "code", "message", "details", "innererror" } }`.
- Compiled dependency intent files: `requirements/core.txt`, `api.txt`, `prod.txt`, `dev.txt`, `security.txt`.
- Operational excellence model with SLOs, release rings, rollback policy and observability contract.
- Tests converted away from unstable CLI subprocess harness into direct contract tests where possible.
- Pytest coverage executed with plugin autoload disabled and explicit `pytest_cov` plugin to avoid sandbox plugin deadlocks.

Independent gates observed passing in this environment:

- `ruff check src tests scripts`
- `mypy --no-incremental src`
- `pytest -m "not slow"`: 83 passed, 3 deselected
- `pytest -m slow`: 3 passed
- coverage gate: 85.98%, threshold 80%
- schema validation
- frontend quality
- UI asset check
- dependency contracts
- threat model
- Microsoft REST contract
- operational excellence
- automation contract
- test architecture
- bibliography
- science registry
- API smoke
- dynamic environment probe
- OpenAPI export/check
- Bandit medium/high gate
- wheel smoke
- manifest validation
- repo clean

Known environment limitations:

- `pip-audit` remains UNKNOWN when DNS to `pypi.org` is unavailable.
- Docker runtime remains UNKNOWN without a Docker host.
- Full monolithic `verify_release.py` hit sandbox process timeout despite independent gates passing; release evidence therefore remains independent-gate based for this artifact.
