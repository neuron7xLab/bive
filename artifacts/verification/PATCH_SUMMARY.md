# BIVE v0.4.0 operational hardening patch

## Machine-verified closed gates

- `make verify-release` -> `VERIFY_RELEASE_PASS`
- `ruff check src tests scripts` -> pass
- `mypy src` -> pass
- `pytest -q` -> 29 passed
- `pytest --cov=bive --cov-fail-under=80` -> 85.18%
- `python scripts/validate_schemas.py --strict --instances` -> pass
- `python scripts/wheel_smoke.py` -> wheel contains API/UI assets and imports `bive.api` from installed wheel
- `bandit -q -r src scripts -c pyproject.toml -ll` -> pass with explicit B104 waiver on production bind

## Remediated blocker classes

- production wheel missing UI/static package data
- version drift between package metadata and API health
- Python 3.10 type incompatibility from `datetime.UTC`
- API schema/runtime drift on extra fields
- missing input size and segment/text limits
- no production-mode auth guard
- missing readiness/liveness endpoints
- raw CLI tracebacks for expected input failures
- lint/typecheck not included in release gate
- schema syntax-only validation
- dirty repository archive with caches/local SQLite

## Still fail-closed / not proven in this environment

- dependency CVE audit: `pip-audit` could not resolve `pypi.org`; see `artifacts/security/pip-audit.attempt.log`
- Docker runtime: Docker executable unavailable in audit environment
- external deployment target/SLO/threat model: UNKNOWN
