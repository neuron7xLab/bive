# Stage 5 Code/Test Hardening Summary

## Scope

Stage 5 focused on executable code solidity and regression depth, not product copy or cosmetic UI work.

## Code changes

- `src/bive/adapters/base.py`: added shared timeout-bounded adapter command runner and bounded error messages.
- `src/bive/adapters/openface_adapter.py`: routed OpenFace execution through the shared adapter runner.
- `src/bive/adapters/opensmile_adapter.py`: routed openSMILE execution through the shared adapter runner.
- `src/bive/adapters/whisper_adapter.py`: routed Whisper execution through the shared adapter runner.
- `src/bive/settings.py`: replaced import-time env parsing with runtime-safe default factories and explicit config errors.
- `src/bive/storage.py`: added schema metadata table, schema version contract and stats exposure.
- `src/bive/api.py`: counted early middleware rejections in metrics and exposed storage schema version through system status.
- `src/bive/api_models.py`: added `schema_version` to `StorageStatsResponse`.
- `src/bive/cli.py`: converted eval input schema failures into controlled `BIVE_ERROR INVALID_EVAL_SCHEMA` responses.
- `scripts/verify_release.py`: added process-group timeout handling and stable release gate logging.
- `Makefile`: changed typecheck to `mypy --no-incremental src` to avoid repo-local mypy cache artifacts.

## Test changes

- `tests/test_adapters_contract.py`: adapter timeout, bounded stderr, missing executable and timeout propagation.
- `tests/test_api_security_runtime.py`: staging token enforcement, readiness failure without token and early rejection metrics.
- `tests/test_storage_operational_contract.py`: schema version and concurrent write behavior.
- `tests/test_cli_strict_contract.py`: controlled CLI eval failures.

## Machine evidence

- `pytest -q`: 46 passed.
- `pytest --cov=bive --cov-report=term-missing --cov-fail-under=80`: 86.10% total coverage.
- `ruff check src tests scripts`: PASS.
- `mypy --no-incremental src`: PASS.
- `bandit -q -r src scripts -c pyproject.toml -ll`: PASS.
- `python scripts/wheel_smoke.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/verify_release.py`: VERIFY_RELEASE_PASS for stable gates.
