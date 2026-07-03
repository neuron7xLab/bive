from __future__ import annotations

import pytest

from bive.calibration_metrics import (
    IsotonicCalibrator,
    PlattCalibrator,
    average_precision,
    brier_score,
    evaluate_probabilities,
    expected_calibration_error,
    reliability_bins,
    roc_auc,
)


def test_roc_auc_perfect_and_chance() -> None:
    assert roc_auc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0
    assert roc_auc([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]) == 0.0
    assert roc_auc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]) == pytest.approx(0.5)


def test_roc_auc_single_class_is_chance() -> None:
    assert roc_auc([1, 1, 1], [0.2, 0.5, 0.9]) == 0.5


def test_average_precision_perfect() -> None:
    assert average_precision([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == pytest.approx(1.0)


def test_brier_bounds() -> None:
    assert brier_score([1, 0], [1.0, 0.0]) == 0.0
    assert brier_score([1, 0], [0.0, 1.0]) == 1.0


def test_ece_zero_for_perfect_calibration() -> None:
    # Predictions equal to base rate within each bin -> zero calibration error.
    labels = [0, 0, 1, 1]
    probs = [0.0, 0.0, 1.0, 1.0]
    assert expected_calibration_error(labels, probs, n_bins=10) == pytest.approx(0.0)


def test_reliability_bins_partition_all() -> None:
    labels = [0, 1, 0, 1]
    probs = [0.05, 0.95, 0.45, 0.55]
    bins = reliability_bins(labels, probs, n_bins=10)
    assert sum(b.count for b in bins) == len(labels)


def test_isotonic_is_monotonic_and_bounded() -> None:
    scores = [0.1, 0.2, 0.3, 0.6, 0.7, 0.9]
    labels = [0, 0, 0, 1, 1, 1]
    cal = IsotonicCalibrator.fit(scores, labels)
    out = cal.predict([0.0, 0.25, 0.5, 0.65, 1.0])
    assert all(0.0 <= p <= 1.0 for p in out)
    assert out == sorted(out)  # non-decreasing


def test_platt_moves_toward_labels() -> None:
    scores = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    labels = [0, 0, 0, 1, 1, 1]
    cal = PlattCalibrator.fit(scores, labels)
    assert cal.predict_one(0.9) > cal.predict_one(0.1)


def test_evaluate_probabilities_shape() -> None:
    report = evaluate_probabilities([0, 1, 0, 1], [0.2, 0.8, 0.3, 0.7])
    d = report.to_dict()
    assert d["n"] == 4
    assert 0.0 <= d["roc_auc"] <= 1.0
    assert "reliability" in d


def test_validation_errors() -> None:
    with pytest.raises(ValueError):
        roc_auc([0, 1], [0.5])
    with pytest.raises(ValueError):
        brier_score([], [])
    with pytest.raises(ValueError):
        expected_calibration_error([2, 0], [0.5, 0.5])
