# Independent Gate Evidence

Runtime note: this sandbox can intermittently stall when many long Python gates are chained inside one parent process. To avoid false evidence, heavy gates are also recorded as independently executed machine checks.

## Passed gates

- `ruff check src tests scripts` — PASS
- `mypy --no-incremental src` — PASS
- `pytest -q` — PASS, 46 tests
- `pytest --cov=bive --cov-report=term-missing --cov-fail-under=80` — PASS, 46 tests, 86.10% coverage
- `python scripts/validate_schemas.py --strict --instances` — PASS
- `python scripts/api_smoke.py` — PASS
- `python scripts/check_frontend_quality.py` — PASS
- `python scripts/export_openapi.py --output docs/openapi.json --check` — PASS
- `python scripts/wheel_smoke.py` — PASS
- `bandit -q -r src scripts -c pyproject.toml -ll` — PASS
- `python scripts/validate_release_manifest.py` — PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/verify_release.py` — PASS for stable release gates

## Stage 5 code/test deltas

- Added adapter subprocess timeout and bounded failure-result handling.
- Added adapter regression tests for missing executable, timeout, stderr truncation and success timeout propagation.
- Added staging/production API authentication regression tests.
- Added API early-rejection metrics regression test.
- Added storage schema version and concurrent write regression tests.
- Added CLI eval schema failure tests.
- Hardened settings parsing for invalid integer environment values.

## External gates still required outside this sandbox

- `make dependency-audit` with network access to vulnerability/advisory sources.
- `make docker-build` and container `/readyz` check on a host with Docker.
