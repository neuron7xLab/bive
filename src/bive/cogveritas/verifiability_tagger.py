"""Verifiability tagger — extract externally checkable claims (no verdict).

Answers only: *which claims can be checked against external facts?* Never *is the
speaker lying?* Deterministic by default (regex/lexicon); an optional spaCy
``en_core_web_trf`` path is used for named entities when installed, with a
deterministic fallback so results are reproducible without it.

Grounding: the Verifiability Approach (Nahari, Vrij & Fisher 2014) — truthful
accounts contain more checkable detail. Here that detail is a *review signal*,
not a deception score.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from importlib import util as _import_util

from .lang import LanguagePack, detect_language, pack_for_code, pack_for_text

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

_MIN_TOKENS = 3


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    tokens: list[str] = field(default_factory=list)
    lang: str = "en"
    speaker: str = ""


@dataclass(frozen=True)
class VerifiabilityFeatures:
    count_verifiable: int
    count_unverifiable: int
    verifiability_ratio: float
    detail_density: float
    named_entity_count: int
    temporal_anchor_count: int
    spatial_anchor_count: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "count_verifiable": self.count_verifiable,
            "count_unverifiable": self.count_unverifiable,
            "verifiability_ratio": round(self.verifiability_ratio, 6),
            "detail_density": round(self.detail_density, 6),
            "named_entity_count": self.named_entity_count,
            "temporal_anchor_count": self.temporal_anchor_count,
            "spatial_anchor_count": self.spatial_anchor_count,
        }

    def vector(self) -> list[float]:
        return [
            float(self.count_verifiable),
            float(self.count_unverifiable),
            self.verifiability_ratio,
            self.detail_density,
            float(self.named_entity_count),
            float(self.temporal_anchor_count),
            float(self.spatial_anchor_count),
        ]


FEATURE_ORDER = [
    "count_verifiable",
    "count_unverifiable",
    "verifiability_ratio",
    "detail_density",
    "named_entity_count",
    "temporal_anchor_count",
    "spatial_anchor_count",
]

_SPACY_AVAILABLE = _import_util.find_spec("spacy") is not None


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def segment_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(normalize_text(text)) if s.strip()]


def _cid(text: str, idx: int) -> str:
    return f"claim:{idx}:{hashlib.sha256(text.encode()).hexdigest()[:8]}"


def segment_claims(sentence: str, pack: LanguagePack | None = None) -> list[Claim]:
    """One claim per sentence (a stable, transparent unit). Sub-clause splitting
    is deferred; sentences are the reviewable atom. Tokenised in the given
    language (auto-detected when ``pack`` is omitted)."""
    p = pack or pack_for_text(sentence)
    toks = p.word.findall(sentence)
    if len(toks) < _MIN_TOKENS:
        return []
    return [Claim(_cid(sentence, 0), sentence, toks, p.code)]


def extract_named_entities(text: str, pack: LanguagePack | None = None) -> list[str]:
    """spaCy entities if available (English only), else a deterministic
    proper-noun/number proxy in the detected language."""
    p = pack or pack_for_text(text)
    if p.code == "en" and _SPACY_AVAILABLE:  # pragma: no cover - optional heavy path
        try:
            import spacy  # noqa: PLC0415

            nlp = spacy.load("en_core_web_trf")
            return [ent.text for ent in nlp(text).ents]
        except Exception:
            pass
    return _proper_names(text, p) + p.numeric.findall(text)


def _proper_names(text: str, pack: LanguagePack) -> list[str]:
    """Proper-noun proxy matches, minus capitalised function words (This, There,
    Maybe, він, там…) and opinion markers (Здавалося, Казалось…) the regex
    over-captures at sentence start — those are not named-entity anchors and must not
    make an opinion read as externally checkable. A word cannot be both the opinion
    cue and a named entity."""
    return [
        m
        for m in pack.proper.findall(text)
        if m.lower() not in pack.stop_names and m.lower() not in pack.unverifiable
    ]


def classify_claim_verifiability(claim: Claim) -> str:
    """externally_checkable / not_externally_checkable / insufficient_context."""
    if len(claim.tokens) < _MIN_TOKENS:
        return "insufficient_context"
    p = pack_for_code(claim.lang)
    checkable = (
        len(_proper_names(claim.text, p))
        + len(p.numeric.findall(claim.text))
        + len(p.temporal.findall(claim.text))
    )
    lowered = [t.lower() for t in claim.tokens]
    spatial = sum(t in p.spatial for t in lowered)
    opinion = sum(t in p.unverifiable for t in lowered)
    # A record-producing action (signed/paid/called…) is a checkable signal even
    # without a named-entity anchor — the action leaves an external record.
    action = sum(any(t.startswith(stem) for stem in p.actions) for t in lowered)
    positive = checkable + spatial + action
    if positive >= 1 and positive >= opinion:
        return "externally_checkable"
    return "not_externally_checkable"


def build_feature_vector(claims: list[Claim]) -> VerifiabilityFeatures:
    total_tokens = sum(len(c.tokens) for c in claims) or 1
    verifiable = 0
    unverifiable = 0
    ne = 0
    temporal = 0
    spatial = 0
    for claim in claims:
        p = pack_for_code(claim.lang)
        label = classify_claim_verifiability(claim)
        if label == "externally_checkable":
            verifiable += 1
        elif label == "not_externally_checkable":
            unverifiable += 1
        ne += len(_proper_names(claim.text, p)) + len(p.numeric.findall(claim.text))
        temporal += len(p.temporal.findall(claim.text))
        spatial += sum(t.lower() in p.spatial for t in claim.tokens)
    denom = verifiable + unverifiable or 1
    return VerifiabilityFeatures(
        count_verifiable=verifiable,
        count_unverifiable=unverifiable,
        verifiability_ratio=verifiable / denom,
        detail_density=(ne + temporal + spatial) / total_tokens,
        named_entity_count=ne,
        temporal_anchor_count=temporal,
        spatial_anchor_count=spatial,
    )


def build_provenance_nodes(claims: list[Claim]) -> list[dict[str, object]]:
    return [
        {
            "claim_id": c.claim_id,
            "text": c.text,
            "verifiability": classify_claim_verifiability(c),
            "entities": extract_named_entities(c.text, pack_for_code(c.lang))[:12],
        }
        for c in claims
    ]


def analyze(text: str) -> tuple[VerifiabilityFeatures, list[Claim]]:
    # Detect language once per document so every claim shares one anchor set.
    pack = pack_for_code(detect_language(text))
    claims: list[Claim] = []
    for sent in segment_sentences(text):
        claims.extend(segment_claims(sent, pack))
    return build_feature_vector(claims), claims


def feature_schema_sha256() -> str:
    return hashlib.sha256("|".join(FEATURE_ORDER).encode()).hexdigest()
