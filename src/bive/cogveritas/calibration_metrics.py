"""Deterministic calibration/discrimination metrics for COGVERITAS.

Builds on BIVE's already-validated, dependency-free primitives
(:mod:`bive.calibration_metrics`) — reused, not reimplemented — and exposes the
exact API the COGVERITAS spec requires, including a 10-bin reliability diagram.
No hidden randomness; the bootstrap is seeded.
"""

from __future__ import annotations

from ..calibration_metrics import (
    bootstrap_interval,
    brier_score,
    expected_calibration_error,
    reliability_bins,
    roc_auc,
)

__all__ = [
    "bootstrap_ci",
    "brier_score",
    "expected_calibration_error",
    "reliability_diagram",
    "roc_auc",
]


def bootstrap_ci(
    labels: list[int], scores: list[float], *, n_boot: int = 1000, seed: int = 20260703
) -> tuple[float, float]:
    """Seeded percentile bootstrap CI for ROC-AUC (deterministic)."""
    interval = bootstrap_interval(roc_auc, labels, scores, n_boot=n_boot, seed=seed)
    return round(interval.lower, 6), round(interval.upper, 6)


def reliability_diagram(labels: list[int], probs: list[float], bins: int = 10) -> dict[str, list[float]]:
    """10-bin reliability diagram: edges, mean predicted, empirical frequency, count."""
    rows = reliability_bins(labels, probs, n_bins=bins)
    edges = [round(i / bins, 6) for i in range(bins + 1)]
    return {
        "bin_edges": edges,
        "mean_predicted": [round(b.mean_confidence, 6) for b in rows],
        "empirical_frequency": [round(b.empirical_accuracy, 6) for b in rows],
        "count": [float(b.count) for b in rows],
    }
