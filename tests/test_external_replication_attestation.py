"""Falsifiers for the external replication attestation gate.

The gate must open the benchmark-grade path ONLY for a real, reproducing, independent
attestation — and reject everything else (self-issued-as-independent, non-reproducing,
malformed). Each test proves one guard fires.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parents[1]


def _gate() -> ModuleType:
    path = _REPO / "scripts" / "external_replication_attest_check.py"
    spec = importlib.util.spec_from_file_location("external_replication_attest_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["external_replication_attest_check"] = module
    spec.loader.exec_module(module)
    return module


def _prereg_and_schema(gate: ModuleType) -> tuple[dict, dict]:
    prereg = gate.load_pre_registration(_REPO)
    schema = json.loads((_REPO / "schemas" / "external_replication_attestation.schema.json").read_text())
    return prereg, schema


def _valid_independent() -> dict:
    return {
        "schema_version": 1,
        "attester": {"name": "Jane Doe Lab", "public_repo": "janedoe/bive-replication", "commit_sha": "abc123"},
        "attester_class": "independent",
        "environment": {"os": "ubuntu-24.04", "python_version": "3.12.3"},
        "data": {"corpus": "Ott Deceptive Opinion Spam", "source_url": "https://myleott.com/op-spam.html"},
        "protocol_ref": "docs/methodology/EXTERNAL_REPLICATION_GUIDE.md@deadbeef",
        "result": {"model": "verbal-science (calibrated)", "roc_auc": 0.749},
        "public_evidence_url": "https://github.com/janedoe/bive-replication/actions/runs/1",
        "attested_at": "2026-07-05",
    }


def test_empty_repo_is_the_honest_default() -> None:
    gate = _gate()
    status = gate.assess(_REPO)
    assert status["attested"] is False
    assert status["rejected"] == []
    assert gate.independent_attestation_present(_REPO) is False


def test_valid_independent_attestation_verifies() -> None:
    gate = _gate()
    prereg, schema = _prereg_and_schema(gate)
    assert gate.validate_attestation(_valid_independent(), prereg, schema) == []


def test_self_issued_as_independent_is_rejected() -> None:
    gate = _gate()
    prereg, schema = _prereg_and_schema(gate)
    att = _valid_independent()
    att["attester"]["public_repo"] = "neuron7xLab/bive"  # the canonical repo cannot be independent
    problems = gate.validate_attestation(att, prereg, schema)
    assert any("canonical repo" in p for p in problems)


def test_non_reproducing_auc_is_rejected() -> None:
    gate = _gate()
    prereg, schema = _prereg_and_schema(gate)
    att = _valid_independent()
    att["result"]["roc_auc"] = 0.90  # outside the pre-registered 95% CI
    problems = gate.validate_attestation(att, prereg, schema)
    assert any("outside pre-registered 95% CI" in p for p in problems)


def test_wrong_model_is_rejected() -> None:
    gate = _gate()
    prereg, schema = _prereg_and_schema(gate)
    att = _valid_independent()
    att["result"]["model"] = "ceiling: tf-idf 1-2gram"
    problems = gate.validate_attestation(att, prereg, schema)
    assert any("headline" in p for p in problems)


def test_malformed_attestation_is_rejected() -> None:
    gate = _gate()
    prereg, schema = _prereg_and_schema(gate)
    att = _valid_independent()
    del att["public_evidence_url"]  # required trust anchor
    problems = gate.validate_attestation(att, prereg, schema)
    assert problems and any("schema" in p for p in problems)


def _mini_root(tmp: Path) -> Path:
    (tmp / "research" / "cogveritas" / "replications").mkdir(parents=True)
    (tmp / "schemas").mkdir()
    for rel in (
        "research/cogveritas/phase0_results.json",
        "research/cogveritas/phase0_provenance.json",
        "schemas/external_replication_attestation.schema.json",
    ):
        shutil.copy(_REPO / rel, tmp / rel)
    return tmp


def test_recorded_independent_attestation_opens_the_path(tmp_path: Path) -> None:
    gate = _gate()
    root = _mini_root(tmp_path)
    (root / "research" / "cogveritas" / "replications" / "janedoe-2026.json").write_text(
        json.dumps(_valid_independent())
    )
    assert gate.independent_attestation_present(root) is True
    assert gate.assess(root)["attested"] is True


def test_fraudulent_attestation_fails_closed(tmp_path: Path) -> None:
    gate = _gate()
    root = _mini_root(tmp_path)
    bad = copy.deepcopy(_valid_independent())
    bad["result"]["roc_auc"] = 0.99  # claims a result it did not reproduce
    (root / "research" / "cogveritas" / "replications" / "bad.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="rejected replication"):
        gate.independent_attestation_present(root)
