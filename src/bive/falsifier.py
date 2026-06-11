from __future__ import annotations

from .models import EvidenceEvent, Modality

DEFAULT_ALTERNATIVES = {
    Modality.TEXT: (
        "imprecise wording rather than deception",
        "translation or dialect mismatch",
        "memory uncertainty",
        "stress-induced simplification",
        "defensive communication under pressure",
    ),
    Modality.AUDIO: (
        "microphone quality or compression artifacts",
        "fatigue, illness, cold, or sleep deprivation",
        "emotional arousal unrelated to deception",
        "background noise or speaker overlap",
    ),
    Modality.VISION: (
        "lighting, camera angle, frame rate, occlusion",
        "cultural gestural variance",
        "neurodivergent or individual baseline variance",
        "stress, trauma, pain, or fatigue unrelated to deception",
    ),
    Modality.CONTEXT: (
        "missing records",
        "timeline ambiguity",
        "source reliability mismatch",
        "outdated or edited external evidence",
    ),
    Modality.SYSTEM: ("pipeline uncertainty", "insufficient evidence", "adapter failure"),
}


def alternatives_for_event(event: EvidenceEvent) -> tuple[str, ...]:
    base = list(DEFAULT_ALTERNATIVES[event.modality])
    if event.limitations:
        base.extend(event.limitations)
    return tuple(dict.fromkeys(base))


def aggregate_alternatives(events: list[EvidenceEvent], limit: int = 8) -> tuple[str, ...]:
    alternatives: list[str] = []
    for event in events:
        alternatives.extend(alternatives_for_event(event))
    return tuple(dict.fromkeys(alternatives))[:limit]
