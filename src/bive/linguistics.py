from __future__ import annotations

import re
from collections import defaultdict

from .ingest import TranscriptSegment
from .models import Claim, EvidenceDirection, EvidenceEvent, Modality, ProvenanceRecord, Signal

HEDGE_TERMS = {
    "maybe",
    "probably",
    "i think",
    "i guess",
    "sort of",
    "kind of",
    "можливо",
    "мабуть",
    "ніби",
    "здається",
    "типу",
    "напевно",
    "скоріше",
    "скорее",
    "кажется",
    "вроде",
}
ABSOLUTE_TERMS = {
    "always",
    "never",
    "everyone",
    "nobody",
    "obviously",
    "clearly",
    "ніколи",
    "завжди",
    "всі",
    "ніхто",
    "очевидно",
    "ясно",
    "никогда",
    "всегда",
    "все",
    "никто",
}
PRESSURE_TERMS = {
    "trust me",
    "believe me",
    "you must",
    "no need to check",
    "не треба перевіряти",
    "повір",
    "вір мені",
    "ти повинен",
    "без перевірки",
    "поверь",
    "не надо проверять",
}
TIME_MARKERS = re.compile(
    r"\b(today|yesterday|tomorrow|now|then|before|after|сьогодні|вчора|завтра|тепер|потім|до|після|сегодня|вчера|завтра)\b",
    re.I,
)
NEGATION_RE = re.compile(r"\b(no|not|never|none|ні|не|ніколи|нет|никогда)\b", re.I)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def split_claim_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|[;\n]+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) >= 3]


def extract_claims(segments: list[TranscriptSegment]) -> list[Claim]:
    claims: list[Claim] = []
    for i, seg in enumerate(segments):
        for j, sentence in enumerate(split_claim_sentences(seg.text)):
            qualifiers = []
            n = normalize_text(sentence)
            if any(t in n for t in HEDGE_TERMS):
                qualifiers.append("hedged")
            if any(t in n for t in ABSOLUTE_TERMS):
                qualifiers.append("absolute")
            if TIME_MARKERS.search(sentence):
                qualifiers.append("temporal")
            claims.append(
                Claim(
                    claim_id=f"claim:{i}:{j}",
                    speaker=seg.speaker,
                    text=sentence,
                    start=seg.start,
                    end=seg.end,
                    source_id=seg.source_id,
                    qualifiers=qualifiers,
                )
            )
    return claims


class LinguisticAnalyzer:
    """Deterministic first-pass language analyzer.

    This is intentionally conservative: it produces evidence events and review questions, not verdicts.
    """

    def analyze(self, claims: list[Claim]) -> tuple[list[Signal], list[EvidenceEvent]]:
        signals: list[Signal] = []
        events: list[EvidenceEvent] = []
        by_speaker: dict[str, list[Claim]] = defaultdict(list)
        for claim in claims:
            by_speaker[claim.speaker].append(claim)
            text = normalize_text(claim.text)
            if any(term in text for term in HEDGE_TERMS):
                events.append(
                    self._event(
                        claim, "linguistic_hedging", "hedged assertion", 0.55, 0.25, "neutral"
                    )
                )
            if any(term in text for term in ABSOLUTE_TERMS):
                events.append(
                    self._event(
                        claim, "absolute_framing", "absolute wording", 0.60, 0.35, "supports"
                    )
                )
            if any(term in text for term in PRESSURE_TERMS):
                events.append(
                    self._event(
                        claim,
                        "verification_pressure",
                        "discourages verification",
                        0.70,
                        0.55,
                        "supports",
                    )
                )
            if TIME_MARKERS.search(text):
                events.append(
                    self._event(
                        claim, "temporal_anchor", "time anchor present", 0.65, 0.25, "neutral"
                    )
                )
        events.extend(self._detect_local_contradictions(by_speaker))
        signals.append(
            Signal(
                signal_id="signal:linguistic_event_count",
                modality=Modality.TEXT,
                name="linguistic_event_count",
                value=len(events),
                confidence=0.8,
                interpretation="Count of conservative linguistic evidence events extracted from claims.",
                limitations=("High count is not deception; it only increases review surface.",),
            )
        )
        return signals, events

    def _event(
        self,
        claim: Claim,
        feature: str,
        value: str,
        confidence: float,
        magnitude: float,
        direction: str,
    ) -> EvidenceEvent:
        return EvidenceEvent(
            event_id=f"event:{feature}:{claim.claim_id}",
            source_id=claim.source_id,
            modality=Modality.TEXT,
            feature=feature,
            value=value,
            confidence=confidence,
            magnitude=magnitude,
            direction=EvidenceDirection(direction),
            timestamp_start=claim.start,
            timestamp_end=claim.end,
            hypothesis_refs=("H_MANIPULATION_RISK", "H_INCONSISTENCY_RISK"),
            limitations=(
                "Language-only cue; must be checked against context and counter-evidence.",
            ),
            provenance=ProvenanceRecord(
                entity_id=claim.claim_id,
                activity="linguistic_feature_extraction",
                agent="bive.linguistics.LinguisticAnalyzer",
                source=claim.source_id,
                parameters={"feature": feature},
            ),
        )

    def _detect_local_contradictions(
        self, by_speaker: dict[str, list[Claim]]
    ) -> list[EvidenceEvent]:
        events: list[EvidenceEvent] = []
        for speaker, claims in by_speaker.items():
            seen_negative: list[Claim] = []
            seen_positive: list[Claim] = []
            for claim in claims:
                text = normalize_text(claim.text)
                tokens = set(re.findall(r"[a-zа-яіїєґ0-9]+", text, re.I))
                if NEGATION_RE.search(text):
                    seen_negative.append(claim)
                else:
                    seen_positive.append(claim)
                for neg in seen_negative:
                    if neg.claim_id == claim.claim_id:
                        continue
                    neg_tokens = set(
                        re.findall(r"[a-zа-яіїєґ0-9]+", normalize_text(neg.text), re.I)
                    )
                    overlap = tokens & neg_tokens
                    if len(overlap) >= 3 and not NEGATION_RE.search(text):
                        events.append(
                            EvidenceEvent(
                                event_id=f"event:local_contradiction:{neg.claim_id}:{claim.claim_id}",
                                source_id=claim.source_id,
                                modality=Modality.TEXT,
                                feature="local_claim_tension",
                                value={
                                    "speaker": speaker,
                                    "claim_a": neg.text,
                                    "claim_b": claim.text,
                                    "overlap": sorted(overlap),
                                },
                                confidence=0.78,
                                magnitude=0.82,
                                direction=EvidenceDirection.SUPPORTS,
                                timestamp_start=claim.start,
                                timestamp_end=claim.end,
                                hypothesis_refs=("H_INCONSISTENCY_RISK",),
                                limitations=(
                                    "Lexical overlap heuristic; requires semantic and factual review.",
                                ),
                                provenance=ProvenanceRecord(
                                    entity_id=f"{neg.claim_id}|{claim.claim_id}",
                                    activity="local_contradiction_scan",
                                    agent="bive.linguistics.LinguisticAnalyzer",
                                    source=claim.source_id,
                                ),
                            )
                        )
            _ = seen_positive
        return events
