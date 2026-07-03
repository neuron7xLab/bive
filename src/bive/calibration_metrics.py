"""Calibration and discrimination metrics for probabilistic scores.

A verification system "does not lie" only if the numbers it emits mean what they
appear to mean. This module provides the standard, dependency-free apparatus to
measure that:

- Discrimination — how well scores rank positives above negatives:
  ROC-AUC (Mann-Whitney U form) and average precision (PR-AUC).
- Calibration — whether a score of ``p`` actually corresponds to a ``p`` rate of
  positives: Brier score, Expected Calibration Error (ECE) and a reliability
  diagram (binned confidence vs. accuracy).
- Calibrators that turn raw scores into calibrated probabilities:
  :class:`IsotonicCalibrator` (monotonic, pool-adjacent-violators) and
  :class:`PlattCalibrator` (logistic). Both are pure Python and deterministic.

Everything here is total and side-effect free, so results are reproducible.
"""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Callable
from dataclasses import dataclass, field
from math import exp, log
from random import Random


def _validate(labels: list[int], scores: list[float]) -> None:
    if len(labels) != len(scores):
        raise ValueError("labels and scores must have equal length")
    if not labels:
        raise ValueError("empty input")
    if any(y not in (0, 1) for y in labels):
        raise ValueError("labels must be 0 or 1")


def brier_score(labels: list[int], probs: list[float]) -> float:
    """Mean squared error between predicted probabilities and outcomes (lower better)."""
    _validate(labels, probs)
    return sum((p - y) ** 2 for y, p in zip(labels, probs, strict=True)) / len(labels)


def roc_auc(labels: list[int], scores: list[float]) -> float:
    """ROC-AUC via the Mann-Whitney U statistic with tie-aware average ranks."""
    _validate(labels, scores)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        # AUC is undefined with a single class; report chance rather than crash.
        return 0.5
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1  # 1-based average rank across the tie block
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    rank_sum_pos = sum(ranks[i] for i in range(len(labels)) if labels[i] == 1)
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def average_precision(labels: list[int], scores: list[float]) -> float:
    """Area under the precision-recall curve (PR-AUC), interpolation-free."""
    _validate(labels, scores)
    n_pos = sum(labels)
    if n_pos == 0:
        return 0.0
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    tp = 0
    fp = 0
    ap = 0.0
    prev_recall = 0.0
    for idx in order:
        if labels[idx] == 1:
            tp += 1
        else:
            fp += 1
        recall = tp / n_pos
        precision = tp / (tp + fp)
        ap += precision * (recall - prev_recall)
        prev_recall = recall
    return ap


@dataclass(frozen=True)
class ReliabilityBin:
    lower: float
    upper: float
    count: int
    mean_confidence: float
    empirical_accuracy: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "lower": round(self.lower, 4),
            "upper": round(self.upper, 4),
            "count": self.count,
            "mean_confidence": round(self.mean_confidence, 4),
            "empirical_accuracy": round(self.empirical_accuracy, 4),
        }


def reliability_bins(labels: list[int], probs: list[float], n_bins: int = 10) -> list[ReliabilityBin]:
    """Bin predictions and report mean confidence vs. empirical accuracy per bin."""
    _validate(labels, probs)
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")
    bins: list[ReliabilityBin] = []
    for b in range(n_bins):
        lo = b / n_bins
        hi = (b + 1) / n_bins
        members = [
            (y, p)
            for y, p in zip(labels, probs, strict=True)
            if (p >= lo and p < hi) or (b == n_bins - 1 and p == hi)
        ]
        if not members:
            bins.append(ReliabilityBin(lo, hi, 0, 0.0, 0.0))
            continue
        conf = sum(p for _, p in members) / len(members)
        acc = sum(y for y, _ in members) / len(members)
        bins.append(ReliabilityBin(lo, hi, len(members), conf, acc))
    return bins


def expected_calibration_error(labels: list[int], probs: list[float], n_bins: int = 10) -> float:
    """ECE: sample-weighted mean gap between confidence and accuracy across bins."""
    total = len(labels)
    return sum(
        (b.count / total) * abs(b.mean_confidence - b.empirical_accuracy)
        for b in reliability_bins(labels, probs, n_bins)
    )


@dataclass(frozen=True)
class IsotonicCalibrator:
    """Monotonic (non-decreasing) calibration via pool-adjacent-violators."""

    x: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)

    @classmethod
    def fit(cls, scores: list[float], labels: list[int]) -> IsotonicCalibrator:
        _validate(labels, scores)
        order = sorted(range(len(scores)), key=lambda i: scores[i])
        xs = [scores[i] for i in order]
        # Pool-adjacent-violators on the label sequence sorted by score.
        values = [float(labels[i]) for i in order]
        weights = [1.0] * len(values)
        blocks: list[list[float]] = [[v, w] for v, w in zip(values, weights, strict=True)]
        merged: list[list[float]] = []
        for block in blocks:
            merged.append(block)
            while len(merged) > 1 and merged[-2][0] > merged[-1][0]:
                v2, w2 = merged.pop()
                v1, w1 = merged.pop()
                w = w1 + w2
                merged.append([(v1 * w1 + v2 * w2) / w, w])
        fitted: list[float] = []
        for block in merged:
            fitted.extend([block[0]] * int(block[1]))
        # Collapse to breakpoints keyed by the sorted unique scores.
        bx: list[float] = []
        by: list[float] = []
        for xi, yi in zip(xs, fitted, strict=True):
            if bx and xi == bx[-1]:
                by[-1] = yi
            else:
                bx.append(xi)
                by.append(yi)
        return cls(bx, by)

    def predict_one(self, score: float) -> float:
        if not self.x:
            return score
        if score <= self.x[0]:
            return self.y[0]
        if score >= self.x[-1]:
            return self.y[-1]
        idx = bisect_right(self.x, score) - 1
        x0, x1 = self.x[idx], self.x[idx + 1]
        y0, y1 = self.y[idx], self.y[idx + 1]
        if x1 == x0:
            return y1
        t = (score - x0) / (x1 - x0)
        return y0 + t * (y1 - y0)

    def predict(self, scores: list[float]) -> list[float]:
        return [self.predict_one(s) for s in scores]


@dataclass(frozen=True)
class PlattCalibrator:
    """Logistic (Platt) calibration: p = sigmoid(a * score + b)."""

    a: float = 1.0
    b: float = 0.0

    @classmethod
    def fit(
        cls, scores: list[float], labels: list[int], iterations: int = 500, lr: float = 0.1
    ) -> PlattCalibrator:
        _validate(labels, scores)
        a, b = 1.0, 0.0
        n = len(scores)
        for _ in range(iterations):
            ga = 0.0
            gb = 0.0
            for s, y in zip(scores, labels, strict=True):
                p = 1.0 / (1.0 + exp(-(a * s + b)))
                ga += (p - y) * s
                gb += p - y
            a -= lr * ga / n
            b -= lr * gb / n
        return cls(a, b)

    def predict_one(self, score: float) -> float:
        return 1.0 / (1.0 + exp(-(self.a * score + self.b)))

    def predict(self, scores: list[float]) -> list[float]:
        return [self.predict_one(s) for s in scores]


@dataclass(frozen=True)
class CalibrationReport:
    n: int
    positives: int
    roc_auc: float
    average_precision: float
    brier: float
    ece: float
    log_loss: float
    reliability: list[ReliabilityBin]

    def to_dict(self) -> dict[str, object]:
        return {
            "n": self.n,
            "positives": self.positives,
            "roc_auc": round(self.roc_auc, 4),
            "average_precision": round(self.average_precision, 4),
            "brier": round(self.brier, 4),
            "ece": round(self.ece, 4),
            "log_loss": round(self.log_loss, 4),
            "reliability": [b.to_dict() for b in self.reliability],
        }


@dataclass(frozen=True)
class Interval:
    point: float
    lower: float
    upper: float
    resamples: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "point": round(self.point, 4),
            "lower": round(self.lower, 4),
            "upper": round(self.upper, 4),
            "resamples": self.resamples,
        }


def bootstrap_interval(
    metric: Callable[[list[int], list[float]], float],
    labels: list[int],
    scores: list[float],
    *,
    n_boot: int = 1000,
    seed: int = 20260703,
    alpha: float = 0.05,
) -> Interval:
    """Deterministic percentile bootstrap CI for a metric (seeded, reproducible).

    Zero-trust posture: never report a point estimate as if it were certain.
    Degenerate single-class resamples are skipped so metrics stay defined.
    """
    _validate(labels, scores)
    rng = Random(seed)
    n = len(labels)
    stats: list[float] = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        bl = [labels[i] for i in idx]
        if sum(bl) in (0, n):
            continue
        bs = [scores[i] for i in idx]
        stats.append(metric(bl, bs))
    point = metric(labels, scores)
    if not stats:
        return Interval(point, point, point, 0)
    stats.sort()
    lo = stats[max(0, int(alpha / 2 * len(stats)))]
    hi = stats[min(len(stats) - 1, int((1 - alpha / 2) * len(stats)))]
    return Interval(point, lo, hi, len(stats))


def _log_loss(labels: list[int], probs: list[float]) -> float:
    eps = 1e-12
    total = 0.0
    for y, p in zip(labels, probs, strict=True):
        p = min(max(p, eps), 1 - eps)
        total += -(y * log(p) + (1 - y) * log(1 - p))
    return total / len(labels)


def evaluate_probabilities(
    labels: list[int], probs: list[float], n_bins: int = 10
) -> CalibrationReport:
    """Full discrimination + calibration report for probabilistic predictions."""
    _validate(labels, probs)
    return CalibrationReport(
        n=len(labels),
        positives=sum(labels),
        roc_auc=roc_auc(labels, probs),
        average_precision=average_precision(labels, probs),
        brier=brier_score(labels, probs),
        ece=expected_calibration_error(labels, probs, n_bins),
        log_loss=_log_loss(labels, probs),
        reliability=reliability_bins(labels, probs, n_bins),
    )
