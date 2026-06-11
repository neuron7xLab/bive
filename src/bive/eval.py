from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryEvalResult:
    n: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    false_negative_rate: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "n": self.n,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate,
        }


def safe_div(a: float, b: float) -> float:
    return 0.0 if b == 0 else a / b


def evaluate_binary(labels: list[int], predictions: list[int]) -> BinaryEvalResult:
    if len(labels) != len(predictions):
        raise ValueError("labels and predictions must have the same length")
    if not labels:
        raise ValueError("empty evaluation input")
    tp = sum(1 for y, p in zip(labels, predictions, strict=True) if y == 1 and p == 1)
    tn = sum(1 for y, p in zip(labels, predictions, strict=True) if y == 0 and p == 0)
    fp = sum(1 for y, p in zip(labels, predictions, strict=True) if y == 0 and p == 1)
    fn = sum(1 for y, p in zip(labels, predictions, strict=True) if y == 1 and p == 0)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)
    return BinaryEvalResult(
        n=len(labels),
        accuracy=round(safe_div(tp + tn, len(labels)), 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        false_positive_rate=round(safe_div(fp, fp + tn), 4),
        false_negative_rate=round(safe_div(fn, fn + tp), 4),
    )
