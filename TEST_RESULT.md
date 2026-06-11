# Test Result

Generated for BIVE v0.4.0 Stage 11 industrial product packaging.

## Machine-verified gates in this environment

- `pytest -q tests/test_product_operating_model.py`: 6 passed.
- `pytest -q -m "not slow"`: pass, 105 tests executed.
- `pytest -q -m slow`: 7 passed.
- `pytest -p pytest_cov -q -m "not slow" --cov=bive --cov-fail-under=80`: pass, total coverage 85.89%.
- `python scripts/validate_product_operating_model.py`: `PRODUCT_READINESS_PASS`.
- `python scripts/validate_aos_kernel.py`: `AOS_KERNEL_PASS`.
- `python scripts/validate_cognitive_control_plane.py`: `COGNITIVE_CONTROL_PASS`.
- `python scripts/validate_neurocognitive_protocol.py`: `NEUROCOGNITIVE_PROTOCOL_PASS`.
- `python scripts/validate_microsoft_rest_contract.py`: `MICROSOFT_REST_CONTRACT_PASS`.
- `python scripts/validate_operational_excellence.py`: `OPERATIONAL_EXCELLENCE_PASS`.
- `python scripts/validate_dependency_contracts.py`: `DEPENDENCY_CONTRACT_PASS`.
- `python scripts/validate_automation_contract.py`: `AUTOMATION_CONTRACT_PASS`.
- `python scripts/validate_test_architecture.py`: `TEST_ARCHITECTURE_PASS`.
- `python scripts/validate_bibliography.py`: `BIBLIOGRAPHY_PASS`.
- `python scripts/validate_threat_model.py`: `THREAT_MODEL_PASS`.
- `python scripts/export_openapi.py --output docs/openapi.json`: `OPENAPI_PASS`.
- `python scripts/check_ui_assets.py`: `UI_ASSET_PASS`.
- `python scripts/check_frontend_quality.py`: `FRONTEND_QUALITY_PASS`.
- `python scripts/validate_schemas.py --strict --instances`: schema and instance validation pass.
- `python scripts/api_smoke.py`: `API_SMOKE_PASS`.

## Environment-limited gates

- `ruff`: requires local `ruff` executable.
- `mypy`: requires local `mypy` executable.
- `pip-audit`: network/CVE audit remains environment-dependent.
- Docker runtime: requires Docker host.

## Status

Open-source product candidate: STRONG. Production deployment: YELLOW/BLOCKED until CVE audit, Docker runtime, deployment smoke and human-impact review close.
