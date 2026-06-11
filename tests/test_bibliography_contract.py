from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
def test_bibliography_script_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_bibliography.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout
    assert "BIBLIOGRAPHY_PASS" in result.stdout


@pytest.mark.slow
def test_bibliography_artifact_has_required_domains() -> None:
    subprocess.run([sys.executable, "scripts/validate_bibliography.py"], check=True)
    data = json.loads(Path("artifacts/verification/BIBLIOGRAPHY_VALIDATION.json").read_text())
    assert data["references"] >= 14
    assert "neurophysiology / predictive processing" in data["domains"]
    assert "open-source security automation" in data["domains"]


def test_science_registry_has_stage7_reference_depth() -> None:
    data = json.loads(Path("src/bive/resources/science_registry.json").read_text())
    ids = {item["id"] for item in data["references"]}
    assert "friston_2010" in ids
    assert "zadeh_mosei_2018" in ids
    assert "w3c_prov_2013" in ids
    assert "pip_audit_2026" in ids


def test_every_science_reference_has_negative_boundary() -> None:
    data = json.loads(Path("src/bive/resources/science_registry.json").read_text())
    for ref in data["references"]:
        boundary = ref["claim_boundary"].lower()
        assert "not" in boundary or "no " in boundary


def test_bibliography_mentions_registry_identifiers() -> None:
    doc = Path("docs/BIBLIOGRAPHY.md").read_text()
    for ref_id in ["cacioppo_handbook_2007", "perez_rosas_2015", "openssf_scorecard"]:
        assert ref_id in doc


def test_engineering_validation_maps_bibliography_and_dependency_gates() -> None:
    text = Path("docs/ENGINEERING_VALIDATION.md").read_text()
    assert "Bibliography" in text
    assert "Dependencies" in text
    assert "make dependency-contracts" in text
