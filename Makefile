.PHONY: verify verify-release test test-slow coverage lint typecheck schema demo pr-check api api-smoke wheel-smoke ui-check frontend-quality science-registry dynamic-probe determinism-stress simulate red-team security-static dependency-audit license-audit dependency-contracts deps-check deps-compile metadata openapi manifest manifest-check repo-clean automation-contract test-architecture bibliography threat-model microsoft-rest operational-excellence aos-kernel cognitive-control neurocognitive-protocol product-readiness evidence-bundle docker-build docker-run clean

PYTHON ?= python
export PYTHONDONTWRITEBYTECODE := 1

verify: test schema ui-check science-registry aos-kernel dynamic-probe determinism-stress simulate red-team pr-check api-smoke dependency-contracts automation-contract test-architecture bibliography threat-model microsoft-rest operational-excellence cognitive-control neurocognitive-protocol product-readiness
	@echo "VERIFY_PASS"

verify-release:
	PYTHONPATH=src $(PYTHON) scripts/verify_release.py


test:
	PYTHONPATH=src pytest -vv -m "not slow"

test-slow:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src pytest -vv \
		tests/test_automation_contract.py::test_automation_contract_script_passes \
		tests/test_automation_contract.py::test_automation_contract_artifact_lists_release_gates \
		tests/test_bibliography_contract.py::test_bibliography_script_passes \
		tests/test_bibliography_contract.py::test_bibliography_artifact_has_required_domains \
		tests/test_dynamic_environment_probe.py::test_dynamic_environment_probe_script_runs \
		tests/test_release_gate_contract.py::test_evidence_bundle_script_passes_after_prerequisites \
		tests/test_release_gate_contract.py::test_evidence_bundle_records_hashes

coverage:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src pytest -p pytest_cov -m "not slow" --cov=bive --cov-report=term-missing --cov-fail-under=80

lint:
	RUFF_CACHE_DIR=build/ruff-cache PYTHONPATH=src ruff check src tests scripts

typecheck:
	PYTHONPATH=src mypy --no-incremental src

schema:
	PYTHONPATH=src $(PYTHON) scripts/validate_schemas.py --strict --instances

dependency-contracts deps-check:
	PYTHONPATH=src $(PYTHON) scripts/validate_dependency_contracts.py

deps-compile:
	python -m pip install pip-tools
	pip-compile requirements/core.in -o requirements/core.txt
	pip-compile requirements/api.in -o requirements/api.txt
	pip-compile requirements/dev.in -o requirements/dev.txt
	pip-compile requirements/security.in -o requirements/security.txt

pip-sync-dev:
	pip-sync requirements/dev.txt requirements/security.txt

ui-check:
	PYTHONPATH=src $(PYTHON) scripts/check_ui_assets.py

frontend-quality:
	PYTHONPATH=src $(PYTHON) scripts/check_frontend_quality.py

science-registry:
	PYTHONPATH=src $(PYTHON) scripts/validate_science_registry.py

automation-contract:
	PYTHONPATH=src $(PYTHON) scripts/validate_automation_contract.py

test-architecture:
	PYTHONPATH=src $(PYTHON) scripts/validate_test_architecture.py

bibliography:
	PYTHONPATH=src $(PYTHON) scripts/validate_bibliography.py

threat-model:
	PYTHONPATH=src $(PYTHON) scripts/validate_threat_model.py

microsoft-rest:
	PYTHONPATH=src $(PYTHON) scripts/validate_microsoft_rest_contract.py

operational-excellence:
	PYTHONPATH=src $(PYTHON) scripts/validate_operational_excellence.py

aos-kernel:
	PYTHONPATH=src $(PYTHON) scripts/validate_aos_kernel.py

cognitive-control:
	PYTHONPATH=src $(PYTHON) scripts/validate_cognitive_control_plane.py

neurocognitive-protocol:
	PYTHONPATH=src $(PYTHON) scripts/validate_neurocognitive_protocol.py

product-readiness:
	PYTHONPATH=src $(PYTHON) scripts/validate_product_operating_model.py

dynamic-probe:
	PYTHONPATH=src $(PYTHON) scripts/dynamic_environment_probe.py

determinism-stress:
	PYTHONPATH=src $(PYTHON) scripts/determinism_stress.py

api-smoke:
	PYTHONPATH=src $(PYTHON) scripts/api_smoke.py

wheel-smoke:
	PYTHONPATH=src $(PYTHON) scripts/wheel_smoke.py

repo-clean:
	$(PYTHON) scripts/check_repo_clean.py

security-static:
	PYTHONPATH=src bandit -q -r src scripts -c pyproject.toml -ll

dependency-audit:
	mkdir -p artifacts/security
	pip-audit --format=json --output artifacts/security/pip-audit.json

license-audit:
	mkdir -p artifacts/security
	pip-licenses --format=json --output-file artifacts/security/licenses.json

metadata:
	PYTHONPATH=src $(PYTHON) scripts/validate_metadata.py

openapi:
	PYTHONPATH=src $(PYTHON) scripts/export_openapi.py --output docs/openapi.json --check

manifest:
	PYTHONPATH=src $(PYTHON) scripts/generate_manifest.py

manifest-check:
	PYTHONPATH=src $(PYTHON) scripts/validate_release_manifest.py

evidence-bundle:
	PYTHONPATH=src $(PYTHON) scripts/generate_evidence_bundle.py

pr-check:
	PYTHONPATH=src $(PYTHON) scripts/pr_check.py --repo .

simulate:
	PYTHONPATH=src $(PYTHON) -m bive.cli simulate

red-team:
	PYTHONPATH=src $(PYTHON) -m bive.cli red-team

demo:
	PYTHONPATH=src $(PYTHON) -m bive.cli analyze --input samples/demo_transcript.json --output artifacts/local_demo_report.json
	PYTHONPATH=src $(PYTHON) -m bive.cli render --input artifacts/local_demo_report.json --output artifacts/local_demo_report.md

api:
	PYTHONPATH=src uvicorn bive.api:app --host 127.0.0.1 --port 8080 --reload

docker-build:
	docker build -t bive:local .

docker-run:
	docker run --rm -e BIVE_API_TOKEN=local-dev-token -p 8080:8080 bive:local

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov build dist *.egg-info src/*.egg-info .bive artifacts/local_demo_report.*
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
