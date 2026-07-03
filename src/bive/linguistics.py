from __future__ import annotations

import re
from collections import defaultdict

from .ingest import TranscriptSegment
from .models import Claim, EvidenceDirection, EvidenceEvent, Modality, ProvenanceRecord, Signal
from .style_markers import build_style_events

# Function words carry no propositional content; sharing them between two
# sentences is not evidence of a contradiction. Filtering them out is what stops
# the local-tension scan from flagging every pair of first-person sentences.
STOPWORDS = frozenset(
    {
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
        "that", "this", "these", "those", "is", "are", "was", "were", "be",
        "been", "being", "it", "its", "as", "at", "by", "from", "have", "has",
        "had", "do", "does", "did", "will", "would", "can", "could", "should",
        "i", "you", "he", "she", "we", "they", "me", "my", "your", "our", "their",
        "so", "but", "if", "then", "than", "there", "here", "what", "who", "which",
        "when", "how", "all", "any", "some", "just", "now", "about", "up", "out",
        "і", "й", "та", "в", "у", "на", "з", "із", "до", "що", "це", "як", "не",
        "я", "ти", "ми", "ви", "він", "вона", "мене", "мій", "моя", "тому",
    }
)

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


NEGATION_WORDS = frozenset(
    {
        "no", "not", "never", "none", "nor", "cannot", "nobody", "nothing",
        "ні", "не", "ніколи", "нема", "немає", "нет", "никогда", "нельзя",
    }
)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _stem(token: str) -> str:
    """Very light inflectional stemmer so 'receive'/'received' align.

    English-only and deliberately shallow: strip one common verb/plural suffix,
    then a trailing silent 'e', so surface variants of the same predicate share a
    stem for overlap purposes. Non-English tokens pass through unchanged.
    """
    if len(token) <= 4:
        return token
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            token = token[: -len(suffix)]
            break
    if len(token) > 4 and token.endswith("e"):
        token = token[:-1]
    return token


def _content_and_negated(text: str) -> tuple[set[str], set[str]]:
    """Return (content tokens, content tokens under local negation scope).

    A content token is non-stopword and length ≥ 4. It is marked negated when a
    negation word appears within the preceding three tokens — a shallow but
    reliable proxy for "this predicate is denied here".
    """
    content: set[str] = set()
    negated: set[str] = set()
    window = 0
    for token in re.findall(r"[a-zа-яіїєґ0-9']+", text, re.I):
        if token in NEGATION_WORDS or token.endswith("n't"):
            window = 3
            continue
        if token not in STOPWORDS and len(token) >= 4:
            stem = _stem(token)
            content.add(stem)
            if window > 0:
                negated.add(stem)
        if window > 0:
            window -= 1
    return content, negated


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
        events.extend(build_style_events(claims))
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
            # Precompute, per claim: content tokens, and the subset of content
            # tokens that are *locally negated* (a negation word within the
            # preceding three tokens). A genuine local tension is a shared content
            # token asserted in one claim but negated in the other — not merely a
            # lexical overlap that happens to co-occur with a stray "not".
            analysed: list[tuple[Claim, set[str], set[str]]] = []
            for claim in claims:
                content, negated = _content_and_negated(normalize_text(claim.text))
                for prev, prev_content, prev_negated in analysed:
                    overlap = content & prev_content
                    if len(overlap) < 2:
                        continue
                    conflicted = sorted(
                        (overlap & negated) - prev_negated
                        | (overlap & prev_negated) - negated
                    )
                    if not conflicted:
                        continue
                    # The two claims must be substantially *about the same thing*
                    # (high mutual content overlap), otherwise a shared polysemous
                    # verb ("believe", "think") negated in one is not a tension.
                    union = content | prev_content
                    if not union or len(overlap) / len(union) < 0.34:
                        continue
                    events.append(
                        EvidenceEvent(
                            event_id=f"event:local_contradiction:{prev.claim_id}:{claim.claim_id}",
                            source_id=claim.source_id,
                            modality=Modality.TEXT,
                            feature="local_claim_tension",
                            value={
                                "speaker": speaker,
                                "claim_a": prev.text,
                                "claim_b": claim.text,
                                "overlap": sorted(overlap),
                                "polarity_conflict": conflicted,
                            },
                            confidence=0.78,
                            magnitude=0.82,
                            direction=EvidenceDirection.SUPPORTS,
                            timestamp_start=claim.start,
                            timestamp_end=claim.end,
                            hypothesis_refs=("H_INCONSISTENCY_RISK",),
                            limitations=(
                                "Negation-scope heuristic; requires semantic and factual review.",
                            ),
                            provenance=ProvenanceRecord(
                                entity_id=f"{prev.claim_id}|{claim.claim_id}",
                                activity="local_contradiction_scan",
                                agent="bive.linguistics.LinguisticAnalyzer",
                                source=claim.source_id,
                            ),
                        )
                    )
                analysed.append((claim, content, negated))
        return events
