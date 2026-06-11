from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_script(relative: str) -> ModuleType:
    path = Path(relative)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def test_test_architecture_script_passes(capsys) -> None:  # type: ignore[no-untyped-def]
    assert _load_script("scripts/validate_test_architecture.py").main() == 0
    assert "TEST_ARCHITECTURE_PASS" in capsys.readouterr().out


def test_test_architecture_artifact_records_test_count() -> None:
    assert _load_script("scripts/validate_test_architecture.py").main() == 0
    data = json.loads(Path("artifacts/verification/TEST_ARCHITECTURE.json").read_text())
    assert data["test_functions"] >= 70
    assert "tests/test_release_gate_contract.py" in data["files"]


@pytest.mark.slow
def test_evidence_bundle_script_passes_after_prerequisites() -> None:
    dependency_main = _load_script("scripts/validate_dependency_contracts.py").main
    test_architecture_main = _load_script("scripts/validate_test_architecture.py").main
    automation_main = _load_script("scripts/validate_automation_contract.py").main
    bibliography_main = _load_script("scripts/validate_bibliography.py").main
    evidence_main = _load_script("scripts/generate_evidence_bundle.py").main

    assert dependency_main() == 0
    assert test_architecture_main() == 0
    assert automation_main() == 0
    assert bibliography_main() == 0
    if not Path("artifacts/verification/DYNAMIC_ENVIRONMENT_PROBE.json").exists():
        assert _load_script("scripts/dynamic_environment_probe.py").main() == 0
    assert evidence_main() == 0


@pytest.mark.slow
def test_evidence_bundle_records_hashes() -> None:
    evidence_main = _load_script("scripts/generate_evidence_bundle.py").main

    assert evidence_main() == 0
    data = json.loads(Path("artifacts/verification/EVIDENCE_BUNDLE.json").read_text())
    assert data["status"] == "pass"
    assert all(item["sha256"] for item in data["entries"])


def test_release_log_declares_external_unknowns() -> None:
    text = Path("scripts/verify_release.py").read_text()
    assert "External dependency CVE audit" in text
    assert "Docker" in text


def test_test_strategy_sets_minimum_test_depth() -> None:
    text = Path("docs/TEST_STRATEGY.md").read_text()
    assert "at least 70 test functions" in text
    assert "Coverage gate" in text
