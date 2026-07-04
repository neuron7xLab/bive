"""PR-1 gates — Benchmark Card + Contamination Audit."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import benchmark_card as bc  # noqa: E402  (needs scripts/ on sys.path first)
import contamination_audit as ca  # noqa: E402


def test_benchmark_card_live_is_consistent() -> None:
    assert bc.check() == []


def test_contamination_audit_live_is_clean() -> None:
    assert ca.audit() == []


def test_contamination_bites_on_unqualified_high_auc() -> None:
    # A bare high headline with no leakage/cross-corpus framing must be flagged.
    assert ca.unqualified_high_auc("Our model achieves 0.95 AUC on the benchmark.")


def test_contamination_allows_qualified_high_auc() -> None:
    text = "The TF-IDF ceiling reaches 0.95 AUC but collapses cross-corpus to 0.51 (leakage)."
    assert ca.unqualified_high_auc(text) == []


def test_contamination_ignores_low_auc() -> None:
    assert ca.unqualified_high_auc("The interpretable model holds 0.61 out of domain.") == []
