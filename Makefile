.PHONY: verify clean-env verify-bootstrap env-check check-dependencies check-repo-clean repo-clean test test-matrix test-slow coverage lint typecheck schema demo pr-check api api-smoke wheel-smoke ui-check frontend-quality science-registry dynamic-probe determinism-stress simulate red-team security-static dependency-audit license-audit dependency-contracts deps-check deps-compile metadata openapi manifest manifest-check automation-contract test-architecture bibliography threat-model microsoft-rest operational-excellence aos-kernel cognitive-control neurocognitive-protocol product-readiness evidence-bundle docker-build docker-run clean

PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1
export RUFF_CACHE_DIR := build/ruff-cache

verify: test schema ui-check science-registry aos-kernel dynamic-probe determinism-stress simulate red-team pr-check api-smoke dependency-contracts automation-contract test-architecture bibliography threat-model microsoft-rest operational-excellence cognitive-control neurocognitive-protocol product-readiness
	@echo "VERIFY_PASS"

clean-env:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov build dist *.egg-info src/*.egg-info .bive artifacts/local_demo_report.*
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

env-check:
	$(PYTHON) scripts/check_environment.py

verify-bootstrap: clean-env env-check
	$(PYTHON) -m pip install --upgrade pip setuptools==69.5.1 wheel==0.43.0
	$(PYTHON) -m pip install --no-build-isolation -r requirements/core.txt -r requirements/api.txt -r requirements/dev.txt -r requirements/security.txt -e .

check-dependencies: dependency-contracts
	$(PYTHON) -m pip check

check-repo-clean:
	$(PYTHON) -c "import subprocess, sys; out=subprocess.check_output(['git', 'status', '--porcelain']).decode().strip(); print(out) if out else None; sys.exit(1 if out else 0)" || (echo "[FAIL] Worktree dirty. Untracked file leak detected." && exit 1)

repo-clean: check-repo-clean

verify-release: verify-bootstrap check-dependencies check-repo-clean
	$(PYTHON) scripts/verify_release.py


test:
	$(PYTHON) -m pytest -vv -m "not slow"

test-matrix: test

test-slow:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m pytest -vv \
		tests/test_automation_contract.py::test_automation_contract_script_passes \
		tests/test_automation_contract.py::test_automation_contract_artifact_lists_release_gates \
		tests/test_bibliography_contract.py::test_bibliography_script_passes \
		tests/test_bibliography_contract.py::test_bibliography_artifact_has_required_domains \
		tests/test_dynamic_environment_probe.py::test_dynamic_environment_probe_script_runs \
		tests/test_release_gate_contract.py::test_evidence_bundle_script_passes_after_prerequisites \
		tests/test_release_gate_contract.py::test_evidence_bundle_records_hashes

coverage:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m pytest -p pytest_cov -m "not slow" --cov=bive --cov-report=term-missing --cov-fail-under=80

lint:
	$(PYTHON) -m ruff check src tests scripts

typecheck:
	$(PYTHON) -m mypy --no-incremental src

schema:
	$(PYTHON) scripts/validate_schemas.py --strict --instances

dependency-contracts deps-check:
	$(PYTHON) scripts/validate_dependency_contracts.py

deps-compile:
	$(PYTHON) -m pip install pip-tools
	pip-compile requirements/core.in -o requirements/core.txt
	pip-compile requirements/api.in -o requirements/api.txt
	pip-compile requirements/dev.in -o requirements/dev.txt
	pip-compile requirements/security.in -o requirements/security.txt

pip-sync-dev:
	pip-sync requirements/dev.txt requirements/security.txt

ui-check:
	$(PYTHON) scripts/check_ui_assets.py

frontend-quality:
	$(PYTHON) scripts/check_frontend_quality.py

science-registry:
	$(PYTHON) scripts/validate_science_registry.py

automation-contract:
	$(PYTHON) scripts/validate_automation_contract.py

test-architecture:
	$(PYTHON) scripts/validate_test_architecture.py

bibliography:
	$(PYTHON) scripts/validate_bibliography.py

threat-model:
	$(PYTHON) scripts/validate_threat_model.py

microsoft-rest:
	$(PYTHON) scripts/validate_microsoft_rest_contract.py

operational-excellence:
	$(PYTHON) scripts/validate_operational_excellence.py

aos-kernel:
	$(PYTHON) scripts/validate_aos_kernel.py

cognitive-control:
	$(PYTHON) scripts/validate_cognitive_control_plane.py

neurocognitive-protocol:
	$(PYTHON) scripts/validate_neurocognitive_protocol.py

product-readiness:
	$(PYTHON) scripts/validate_product_operating_model.py

dynamic-probe:
	$(PYTHON) scripts/dynamic_environment_probe.py

determinism-stress:
	$(PYTHON) scripts/determinism_stress.py

api-smoke:
	$(PYTHON) scripts/api_smoke.py

wheel-smoke:
	$(PYTHON) -c "import build" || (echo "[FAIL] Packaging tool 'build' is missing. Run make verify-bootstrap first." && exit 1)
	$(PYTHON) -m build
	$(PYTHON) scripts/wheel_smoke.py

security-static:
	$(PYTHON) -m bandit -q -r src scripts -c pyproject.toml -ll

dependency-audit:
	mkdir -p artifacts/security
	$(PYTHON) -m pip_audit --format=json --output artifacts/security/pip-audit.json

license-audit:
	mkdir -p artifacts/security
	$(PYTHON) -m piplicenses --format=json --output-file artifacts/security/licenses.json

metadata:
	$(PYTHON) scripts/validate_metadata.py

openapi:
	$(PYTHON) scripts/export_openapi.py --output docs/openapi.json --check

manifest:
	$(PYTHON) scripts/generate_manifest.py

manifest-check:
	$(PYTHON) scripts/validate_release_manifest.py

evidence-bundle:
	$(PYTHON) scripts/generate_evidence_bundle.py

pr-check:
	$(PYTHON) scripts/pr_check.py --repo .

simulate:
	$(PYTHON) -m bive.cli simulate

red-team:
	$(PYTHON) -m bive.cli red-team

demo:
	$(PYTHON) -m bive.cli analyze --input samples/demo_transcript.json --output artifacts/local_demo_report.json
	$(PYTHON) -m bive.cli render --input artifacts/local_demo_report.json --output artifacts/local_demo_report.md

api:
	$(PYTHON) -m uvicorn bive.api:app --host 127.0.0.1 --port 8080 --reload

docker-build:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "[WARN] Docker engine binary not found on host. Container build skipped."; \
		exit 0; \
	fi; \
	docker build -t bive:local .

docker-run:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "[FAIL] Docker engine binary not found on host. Cannot run container."; \
		exit 1; \
	fi; \
	docker run --rm -e BIVE_API_TOKEN=local-dev-token -p 8080:8080 bive:local

clean: clean-env
