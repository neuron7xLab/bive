"""PR-1 gates — Benchmark Card + Contamination Audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import benchmark_card as bc  # noqa: E402  (needs scripts/ on sys.path first)
import contamination_audit as ca  # noqa: E402


def test_benchmark_card_live_is_consistent() -> None:
    assert bc.check() == []


def test_contamination_audit_live_is_clean() -> None:
    assert ca.audit() == []


def test_benchmark_gate_emits_machine_readable_artifact() -> None:
    assert bc.main() == 0
    art = json.loads(bc.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert art["benchmarks"] and art["benchmarks"][0]["results"]
    # A high headline must carry the contamination flag; the calibrated model must not.
    flags = {r["model"]: r["contamination_flag"] for r in art["benchmarks"][0]["results"]}
    assert any(v for v in flags.values()), "no contamination-flagged ceiling row"


def test_contamination_gate_emits_artifact_with_threshold() -> None:
    assert ca.main() == 0
    art = json.loads(ca.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert art["leakage_threshold"] == 0.85
    assert art["violations"] == []


def test_contamination_bites_on_unqualified_high_auc() -> None:
    # A bare high headline with no leakage/cross-corpus framing must be flagged.
    assert ca.unqualified_high_auc("Our model achieves 0.95 AUC on the benchmark.")


def test_contamination_allows_qualified_high_auc() -> None:
    text = "The TF-IDF ceiling reaches 0.95 AUC but collapses cross-corpus to 0.51 (leakage)."
    assert ca.unqualified_high_auc(text) == []


def test_contamination_ignores_low_auc() -> None:
    assert ca.unqualified_high_auc("The interpretable model holds 0.61 out of domain.") == []
