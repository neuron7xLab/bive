"""Falsifiers for the frozen reference-result integrity gate.

Each test mutates a copy of the real anchored result / provenance and asserts that a
specific integrity invariant fires. If any of these stopped failing, the gate would
be certifying the anchored claim by assertion again.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

_FROZEN = Path("research/cogveritas/phase0_results.json")
_PROV = Path("research/cogveritas/phase0_provenance.json")


def _gate() -> ModuleType:
    path = Path("scripts/reference_result_integrity_check.py")
    spec = importlib.util.spec_from_file_location("reference_result_integrity_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["reference_result_integrity_check"] = module
    spec.loader.exec_module(module)
    return module


def _load() -> tuple[dict, dict, str]:
    gate = _gate()
    results = json.loads(_FROZEN.read_text())
    prov = json.loads(_PROV.read_text())
    return results, prov, gate._sha256(_FROZEN)


def test_real_committed_result_passes() -> None:
    gate = _gate()
    results, prov, sha = _load()
    assert gate.check(results, prov, sha) == []


def test_main_passes_on_committed_data() -> None:
    assert _gate().main() == 0


def test_freeze_pin_catches_result_drift() -> None:
    gate = _gate()
    results, prov, _ = _load()
    problems = gate.check(results, prov, "deadbeef" * 8)
    assert any("sha256" in p and "drift" in p for p in problems)


def test_kill_verdict_is_re_derived_not_trusted() -> None:
    gate = _gate()
    results, prov, sha = _load()
    tampered = copy.deepcopy(results)
    tampered["kill_gate"]["verdict"] = "FAIL"  # lie: auc is well above threshold
    problems = gate.check(tampered, prov, sha)
    assert any("re-derived" in p for p in problems)


def test_baseline_must_be_a_null_control() -> None:
    gate = _gate()
    results, prov, sha = _load()
    tampered = copy.deepcopy(results)
    for row in tampered["results"]:
        if row["model"] == "baseline: length-only":
            row["auc_ci95"] = [0.70, 0.80]  # no longer brackets chance
    problems = gate.check(tampered, prov, sha)
    assert any("null control" in p for p in problems)


def test_headline_must_be_separated_from_baseline() -> None:
    gate = _gate()
    results, prov, sha = _load()
    tampered = copy.deepcopy(results)
    for row in tampered["results"]:
        if row["model"] == "verbal-science (calibrated)":
            row["auc_ci95"] = [0.50, 0.99]  # lower bound touches chance / overlaps baseline
    problems = gate.check(tampered, prov, sha)
    assert any("chance" in p or "overlaps baseline" in p for p in problems)


def test_leakage_ceiling_must_be_declared_contaminated() -> None:
    gate = _gate()
    results, prov, sha = _load()
    tampered = copy.deepcopy(prov)
    tampered["model_roles"]["ceiling"]["contaminated"] = False
    problems = gate.check(results, tampered, sha)
    assert any("contaminated" in p for p in problems)


def test_tier_must_be_anchored() -> None:
    gate = _gate()
    results, prov, sha = _load()
    tampered = copy.deepcopy(prov)
    tampered["evidence_tier"] = "EXTRAPOLATED"
    problems = gate.check(results, tampered, sha)
    assert any("ANCHORED" in p for p in problems)


def test_headline_calibration_is_enforced() -> None:
    gate = _gate()
    results, prov, sha = _load()
    tampered = copy.deepcopy(results)
    for row in tampered["results"]:
        if row["model"] == "verbal-science (calibrated)":
            row["ece"] = 0.42  # uncalibrated
    problems = gate.check(tampered, prov, sha)
    assert any("ece" in p for p in problems)
