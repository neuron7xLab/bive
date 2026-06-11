from __future__ import annotations

from dataclasses import dataclass
from math import exp, log

from .models import EvidenceDirection, EvidenceEvent, Modality
from .weights import DEFAULT_WEIGHTS, ValueWeights, modality_coverage, weighted_event_score

EPSILON = 1e-9


@dataclass(frozen=True)
class CalibrationResult:
    score: float
    uncertainty: float
    support_count: int
    refute_count: int
    modality_count: int
    raw_logit: float
    reliability_mass: float
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, float | int | list[str]]:
        return {
            "score": self.score,
            "uncertainty": self.uncertainty,
            "support_count": self.support_count,
            "refute_count": self.refute_count,
            "modality_count": self.modality_count,
            "raw_logit": self.raw_logit,
            "reliability_mass": self.reliability_mass,
            "notes": list(self.notes),
        }


def _logit(p: float) -> float:
    p = min(max(p, EPSILON), 1 - EPSILON)
    return log(p / (1 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))


def calibrate_hypothesis(
    prior: float, events: list[EvidenceEvent], weights: ValueWeights = DEFAULT_WEIGHTS
) -> CalibrationResult:
    if not events:
        return CalibrationResult(0.0, 1.0, 0, 0, 0, 0.0, 0.0, ("no evidence",))

    support_count = sum(1 for e in events if e.direction == EvidenceDirection.SUPPORTS)
    refute_count = sum(1 for e in events if e.direction == EvidenceDirection.REFUTES)
    modalities = modality_coverage(events)
    reliability_mass = sum(e.confidence * weights.reliability_for(e.modality) for e in events)
    raw = _logit(prior) + sum(weighted_event_score(e, weights) for e in events)

    notes: list[str] = []
    if len(modalities) == 1:
        raw -= weights.single_modality_penalty
        notes.append("single modality penalty applied")
    if refute_count:
        raw -= weights.counterevidence_bonus * min(refute_count, 3)
        notes.append("counterevidence damped escalation")
    if not ({Modality.TEXT, Modality.CONTEXT} & modalities):
        raw -= weights.missing_evidence_penalty
        notes.append("missing text/context evidence penalty")

    score = _sigmoid(raw)
    if len(modalities) == 1 and score > weights.high_confidence_cap_without_multimodal:
        score = weights.high_confidence_cap_without_multimodal
        notes.append("confidence capped without independent modality")

    independent_mass = max(reliability_mass, EPSILON)
    base_uncertainty = min(1.0, 1.0 / (independent_mass**0.5 + 0.35 * len(modalities)))
    conflict_penalty = 0.10 if support_count and refute_count else 0.0
    uncertainty = min(1.0, max(0.12, base_uncertainty + conflict_penalty))

    return CalibrationResult(
        score=round(score, 4),
        uncertainty=round(uncertainty, 4),
        support_count=support_count,
        refute_count=refute_count,
        modality_count=len(modalities),
        raw_logit=round(raw, 4),
        reliability_mass=round(reliability_mass, 4),
        notes=tuple(notes),
    )
