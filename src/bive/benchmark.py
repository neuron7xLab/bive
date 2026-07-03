"""Construct-validity benchmark and calibration for BIVE's risk scores.

This does NOT claim to measure real-world deception — that would require a
validated field corpus and would overclaim. It measures something we *can*
verify: does BIVE's ``inconsistency_risk`` score actually track the presence of
a genuine self-contradiction (a construct we define and can check by
construction)? A screening instrument may only advertise the discrimination and
calibration it has demonstrated; this harness produces exactly those numbers.

The corpus is deliberately balanced and includes hard negatives — texts that
share vocabulary and negation but are *not* contradictions — so the benchmark
rewards precision, not keyword hits. Calibration error is reported both in-sample
and under deterministic 2-fold cross-validation, so the improvement from the
calibrator is an honest out-of-sample figure.
"""

from __future__ import annotations

from dataclasses import dataclass

from .calibration_metrics import (
    IsotonicCalibrator,
    average_precision,
    evaluate_probabilities,
    expected_calibration_error,
    roc_auc,
)
from .ingest import TranscriptSegment
from .report import build_report_from_segments

# (label, segments): label 1 == a genuine same-speaker self-contradiction is
# present; 0 == no contradiction (several are hard negatives that share topic,
# vocabulary or a stray negation without actually contradicting).
CONSTRUCT_CASES: tuple[tuple[int, tuple[tuple[str, str], ...]], ...] = (
    (1, (("s", "I never received that money."), ("s", "I received that money later."))),
    (1, (("s", "I was not in Kyiv yesterday."), ("s", "Yesterday I was in Kyiv at a meeting."))),
    (1, (("s", "I did not sign the contract."), ("s", "I signed the contract myself on Monday."))),
    (1, (("s", "Я не бачив цих документів."), ("s", "Я бачив ці документи минулого тижня."))),
    (1, (("s", "We never discussed the budget."), ("s", "We discussed the budget for hours."))),
    (1, (("s", "The car was not damaged at all."), ("s", "The car was damaged in the accident."))),
    (1, (("s", "I have no connection to that company."), ("s", "I own shares in that company."))),
    (1, (("s", "Nobody entered the building."), ("s", "Two people entered the building at night."))),
    (1, (("s", "Я ніколи не брав ці кошти."), ("s", "Я взяв ці кошти на ремонт офісу."))),
    (1, (("s", "The payment was never made."), ("s", "The payment was made in full."))),
    (1, (("s", "I did not call the agency."), ("s", "I called the agency that afternoon."))),
    (1, (("s", "She was not present at the meeting."), ("s", "She was present and spoke first."))),
    (0, (("s", "I love my country and I care about its future."), ("s", "The economy needs honest work."))),
    (0, (("s", "I believe we have had enough of that today."), ("s", "I do not believe in raising the tariff."))),
    (0, (("s", "The weather in Kyiv was pleasant yesterday."), ("s", "We had a productive meeting there."))),
    (0, (("s", "I received the report on Monday."), ("s", "I reviewed the report on Tuesday."))),
    (0, (("s", "I want you to know all the facts."), ("s", "That is not Nixon speaking, it is an audit."))),
    (0, (("s", "We discussed the budget and agreed."), ("s", "The plan for next year looks solid."))),
    (0, (("s", "I signed the contract on Monday."), ("s", "The contract covered three years of work."))),
    (0, (("s", "Nobody expected the result."), ("s", "The team celebrated the victory together."))),
    (0, (("s", "Я бачив ці документи раніше."), ("s", "Документи стосувалися старого проєкту."))),
    (0, (("s", "The car was parked outside."), ("s", "The meeting ran late into the evening."))),
    (0, (("s", "I did not think it should be charged."), ("s", "I am proud that taxpayers never paid."))),
    (0, (("s", "She spoke first at the meeting."), ("s", "Her presentation was clear and short."))),
)


def score_inconsistency(segments: list[TranscriptSegment]) -> float:
    """Map a transcript to BIVE's inconsistency-risk score in [0, 1]."""
    report = build_report_from_segments(segments)
    for hypothesis in report.hypotheses:
        if hypothesis.label == "inconsistency_risk":
            return hypothesis.score
    return 0.0


@dataclass(frozen=True)
class BenchmarkResult:
    construct: str
    n: int
    positives: int
    roc_auc: float
    average_precision: float
    raw_ece: float
    calibrated_ece_cv: float
    calibrator: dict[str, list[float]]
    note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "construct": self.construct,
            "n": self.n,
            "positives": self.positives,
            "roc_auc": round(self.roc_auc, 4),
            "average_precision": round(self.average_precision, 4),
            "raw_ece": round(self.raw_ece, 4),
            "calibrated_ece_cv": round(self.calibrated_ece_cv, 4),
            "calibrator": self.calibrator,
            "note": self.note,
        }


def _cases() -> tuple[list[int], list[list[TranscriptSegment]]]:
    labels: list[int] = []
    corpus: list[list[TranscriptSegment]] = []
    for label, rows in CONSTRUCT_CASES:
        labels.append(label)
        corpus.append([TranscriptSegment(sp, txt, i, i + 1) for i, (sp, txt) in enumerate(rows)])
    return labels, corpus


def run_construct_benchmark() -> BenchmarkResult:
    """Score the corpus with BIVE, then report discrimination + honest calibration."""
    labels, corpus = _cases()
    scores = [score_inconsistency(segs) for segs in corpus]

    raw_ece = expected_calibration_error(labels, scores, n_bins=5)

    # Deterministic 2-fold cross-validated calibration: fit isotonic on one fold,
    # measure ECE on the held-out fold, average. Even/odd index split keeps both
    # folds class-balanced given the interleaved corpus ordering.
    even = [i for i in range(len(labels)) if i % 2 == 0]
    odd = [i for i in range(len(labels)) if i % 2 == 1]
    cv_eces: list[float] = []
    for train_idx, test_idx in ((even, odd), (odd, even)):
        cal = IsotonicCalibrator.fit(
            [scores[i] for i in train_idx], [labels[i] for i in train_idx]
        )
        test_probs = cal.predict([scores[i] for i in test_idx])
        cv_eces.append(
            expected_calibration_error([labels[i] for i in test_idx], test_probs, n_bins=5)
        )
    calibrated_ece_cv = sum(cv_eces) / len(cv_eces)

    full = IsotonicCalibrator.fit(scores, labels)
    return BenchmarkResult(
        construct="self_contradiction_present",
        n=len(labels),
        positives=sum(labels),
        roc_auc=roc_auc(labels, scores),
        average_precision=average_precision(labels, scores),
        raw_ece=raw_ece,
        calibrated_ece_cv=calibrated_ece_cv,
        calibrator={"x": [round(v, 4) for v in full.x], "y": [round(v, 4) for v in full.y]},
        note=(
            "Construct-validity benchmark: measures whether inconsistency_risk tracks a "
            "verifiable self-contradiction construct, not real-world deception. "
            "Discrimination is rank-based; calibration ECE is 2-fold cross-validated."
        ),
    )


def full_report() -> dict[str, object]:
    result = run_construct_benchmark()
    labels, corpus = _cases()
    scores = [score_inconsistency(segs) for segs in corpus]
    return {
        "benchmark": result.to_dict(),
        "raw_score_report": evaluate_probabilities(labels, scores, n_bins=5).to_dict(),
    }
