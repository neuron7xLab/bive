from __future__ import annotations

from collections import defaultdict

from .calibration import calibrate_hypothesis
from .falsifier import aggregate_alternatives
from .models import EvidenceDirection, EvidenceEvent, Hypothesis, ReviewStatus
from .weights import DEFAULT_WEIGHTS, ValueWeights

HYPOTHESIS_DEFS = {
    "H_INCONSISTENCY_RISK": "Risk that claims contain unresolved contradictions, timeline tensions or semantic incompatibilities.",
    "H_MANIPULATION_RISK": "Risk that communication attempts to reduce verification, pressure interpretation or control the review frame.",
    "H_LINGUISTIC_STYLE_RISK": "Risk implied by linguistic-style markers that population-level research associates with deception (Newman & Pennebaker 2003; Vrij 2008); weak individually and never a person-level verdict.",
    "H_COGNITIVE_LOAD_RISK": "Risk that observed signals suggest high cognitive load, without implying deception.",
    "H_EVIDENCE_GAP_RISK": "Risk that available evidence is too incomplete for reliable assessment.",
}


# Ekman-grounded cue families. Elevation requires either a content contradiction
# or at least two DISTINCT substantive families — Ekman's "no clue to deceit ...
# is foolproof" and "no single sign of deceit". Arousal (affect) and mere context
# never escalate on their own; a mitigation cue is exculpatory.
CUE_FAMILY = {
    "local_claim_tension": "content",
    "verification_pressure": "manipulation",
    "impression_management": "manipulation",
    "absolute_framing": "framing",
    "low_exclusive_words": "style",
    "low_first_person_singular": "style",
    "elevated_motion_verbs": "style",
    "elevated_negative_emotion": "affect",
    "linguistic_hedging": "affect",
    "cognitive_load_markers": "load",
    "temporal_anchor": "context",
    "high_verifiability": "mitigation",
}
NON_ESCALATING_FAMILIES = frozenset({"affect", "context", "mitigation"})


def status_from(
    score: float, uncertainty: float, evidence_count: int, families: frozenset[str] = frozenset()
) -> ReviewStatus:
    if evidence_count < DEFAULT_WEIGHTS.min_independent_events or uncertainty > 0.78:
        return ReviewStatus.INCONCLUSIVE
    substantive = families - NON_ESCALATING_FAMILIES
    has_content = "content" in families
    # Ekman "no single sign of deceit": affect/context cues alone must not elevate.
    if families and not (has_content or len(substantive) >= 2):
        return ReviewStatus.LOW_RISK
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
            support_events = [e for e in h_events if e.direction == EvidenceDirection.SUPPORTS]
            support = tuple(e.event_id for e in support_events)
            refute = tuple(e.event_id for e in h_events if e.direction == EvidenceDirection.REFUTES)
            calibrated = calibrate_hypothesis(0.5, h_events, self.weights)
            notes = list(calibrated.notes)

            families = frozenset(
                CUE_FAMILY.get(e.feature, "other") for e in support_events
            )
            score = calibrated.score
            # Ekman's Othello error: emotional arousal does not tell you its cause.
            # If the only supporting cues are affect/context, do not attribute them
            # to deception — cap the score toward the prior and say so.
            if support_events and families and families <= (NON_ESCALATING_FAMILIES | {"other"}):
                if score > 0.5:
                    score = 0.5
                notes.append(
                    "othello_error_guard: affective/contextual arousal not attributed to deception (Ekman 1985)"
                )
            alternatives = aggregate_alternatives(h_events) + tuple(notes)
            hypotheses.append(
                Hypothesis(
                    hypothesis_id=hid,
                    label=hid.removeprefix("H_").lower(),
                    description=description,
                    prior=0.5,
                    evidence_for=support,
                    evidence_against=refute,
                    score=round(score, 4),
                    uncertainty=calibrated.uncertainty,
                    status=status_from(score, calibrated.uncertainty, len(h_events), families),
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
