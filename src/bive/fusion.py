from __future__ import annotations

from collections import defaultdict

from .calibration import calibrate_hypothesis
from .falsifier import aggregate_alternatives
from .models import EvidenceDirection, EvidenceEvent, Hypothesis, ReviewStatus
from .weights import DEFAULT_WEIGHTS, ValueWeights

HYPOTHESIS_DEFS = {
    "H_INCONSISTENCY_RISK": "Risk that claims contain unresolved contradictions, timeline tensions or semantic incompatibilities.",
    "H_MANIPULATION_RISK": "Risk that communication attempts to reduce verification, pressure interpretation or control the review frame.",
    "H_COGNITIVE_LOAD_RISK": "Risk that observed signals suggest high cognitive load, without implying deception.",
    "H_EVIDENCE_GAP_RISK": "Risk that available evidence is too incomplete for reliable assessment.",
}


def status_from(score: float, uncertainty: float, evidence_count: int) -> ReviewStatus:
    if evidence_count < DEFAULT_WEIGHTS.min_independent_events or uncertainty > 0.78:
        return ReviewStatus.INCONCLUSIVE
    if score >= 0.72 and uncertainty <= 0.58:
        # Even high scores become REVIEW_REQUIRED, never person-level condemnation.
        return ReviewStatus.REVIEW_REQUIRED
    if score >= 0.56:
        return ReviewStatus.REVIEW_REQUIRED
    return ReviewStatus.LOW_RISK


class EvidenceFusionEngine:
    def __init__(self, weights: ValueWeights = DEFAULT_WEIGHTS) -> None:
        self.weights = weights

    def build_hypotheses(self, events: list[EvidenceEvent]) -> list[Hypothesis]:
        grouped: dict[str, list[EvidenceEvent]] = defaultdict(list)
        for event in events:
            for h in event.hypothesis_refs or ("H_EVIDENCE_GAP_RISK",):
                grouped[h].append(event)

        hypotheses: list[Hypothesis] = []
        for hid, description in HYPOTHESIS_DEFS.items():
            h_events = grouped.get(hid, [])
            support = tuple(
                e.event_id for e in h_events if e.direction == EvidenceDirection.SUPPORTS
            )
            refute = tuple(e.event_id for e in h_events if e.direction == EvidenceDirection.REFUTES)
            calibrated = calibrate_hypothesis(0.5, h_events, self.weights)
            alternatives = aggregate_alternatives(h_events) + tuple(calibrated.notes)
            hypotheses.append(
                Hypothesis(
                    hypothesis_id=hid,
                    label=hid.removeprefix("H_").lower(),
                    description=description,
                    prior=0.5,
                    evidence_for=support,
                    evidence_against=refute,
                    score=calibrated.score,
                    uncertainty=calibrated.uncertainty,
                    status=status_from(calibrated.score, calibrated.uncertainty, len(h_events)),
                    alternative_explanations=alternatives,
                )
            )
        return hypotheses

    def final_status(self, hypotheses: list[Hypothesis]) -> ReviewStatus:
        if not hypotheses:
            return ReviewStatus.INVALID_INPUT
        actionable = [h for h in hypotheses if h.status == ReviewStatus.REVIEW_REQUIRED]
        if actionable:
            return ReviewStatus.REVIEW_REQUIRED
        if all(h.status == ReviewStatus.LOW_RISK for h in hypotheses):
            return ReviewStatus.LOW_RISK
        return ReviewStatus.INCONCLUSIVE
