from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from .models import EvidenceDirection, EvidenceEvent, Modality


class ActionMode(str, Enum):
    CALM = "calm"
    BALANCED = "balanced"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class ValueWeights:
    """Deterministic value-function weights.

    The weights are intentionally conservative. BIVE optimizes for truth-seeking under uncertainty,
    not for dramatic accusations. This is the engineering equivalent of not giving a chainsaw to a
    drunk committee, allegedly a difficult constraint for society.
    """

    text_reliability: float = 0.82
    context_reliability: float = 0.90
    audio_reliability: float = 0.62
    vision_reliability: float = 0.58
    system_reliability: float = 0.75
    single_modality_penalty: float = 0.18
    counterevidence_bonus: float = 0.22
    missing_evidence_penalty: float = 0.16
    high_confidence_cap_without_multimodal: float = 0.66
    calm_threshold: float = 0.78
    review_threshold: float = 0.56
    min_independent_events: int = 2

    def reliability_for(self, modality: Modality) -> float:
        return {
            Modality.TEXT: self.text_reliability,
            Modality.CONTEXT: self.context_reliability,
            Modality.AUDIO: self.audio_reliability,
            Modality.VISION: self.vision_reliability,
            Modality.SYSTEM: self.system_reliability,
        }[modality]


DEFAULT_WEIGHTS = ValueWeights()


def modality_coverage(events: Iterable[EvidenceEvent]) -> set[Modality]:
    return {event.modality for event in events}


def weighted_event_score(event: EvidenceEvent, weights: ValueWeights = DEFAULT_WEIGHTS) -> float:
    sign = (
        1.0
        if event.direction == EvidenceDirection.SUPPORTS
        else -1.0
        if event.direction == EvidenceDirection.REFUTES
        else 0.0
    )
    return sign * event.confidence * event.magnitude * weights.reliability_for(event.modality)


def action_mode(
    score: float, uncertainty: float, weights: ValueWeights = DEFAULT_WEIGHTS
) -> ActionMode:
    if score >= weights.calm_threshold and uncertainty <= 0.45:
        return ActionMode.ESCALATE
    if score >= weights.review_threshold and uncertainty <= 0.72:
        return ActionMode.BALANCED
    return ActionMode.CALM
