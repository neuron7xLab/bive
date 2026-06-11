from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
def test_automation_contract_script_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_automation_contract.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout
    assert "AUTOMATION_CONTRACT_PASS" in result.stdout


@pytest.mark.slow
def test_automation_contract_artifact_lists_release_gates() -> None:
    subprocess.run([sys.executable, "scripts/validate_automation_contract.py"], check=True)
    data = json.loads(Path("artifacts/verification/AUTOMATION_CONTRACT.json").read_text())
    assert "coverage" in data["release_gates"]
    assert "dependency-contracts" in data["release_gates"]
    assert "wheel-smoke" in data["release_gates"]


def test_makefile_exposes_industrial_validation_targets() -> None:
    text = Path("Makefile").read_text()
    for target in ["dependency-contracts", "automation-contract", "test-architecture", "bibliography", "evidence-bundle"]:
        assert f"{target}:" in text or f"{target} " in text


def test_ci_includes_supply_chain_automation() -> None:
    text = Path(".github/workflows/ci.yml").read_text()
    assert "actions/dependency-review-action" in text
    assert "ossf/scorecard-action" in text
    assert "make dependency-audit" in text


def test_verify_release_invokes_heavy_gates() -> None:
    text = Path("scripts/verify_release.py").read_text()
    for gate in ["typecheck", "coverage", "security-static", "wheel-smoke", "manifest-check"]:
        assert f'"{gate}"' in text


def test_automation_playbook_documents_local_and_networked_gates() -> None:
    text = Path("docs/AUTOMATION_PLAYBOOK.md").read_text()
    assert "make verify-release" in text
    assert "make dependency-audit" in text
    assert "make docker-build" in text
