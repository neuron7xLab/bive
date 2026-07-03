"""Science-grounded linguistic style markers.

This module computes transcript-level features that the peer-reviewed deception
and credibility literature associates — at the level of *populations*, never a
single person — with deceptive versus truthful language. Each marker is a weak,
reviewable signal, cited to its source and always paired with a limitation. No
marker, alone or combined, is a verdict about a person.

Implemented constructs and their sources (all present in the science registry):

- Linguistic Inquiry style cues — Newman, Pennebaker, Berry & Richards (2003),
  "Lying Words": deceptive accounts tend to use *fewer* first-person singular
  pronouns, *fewer* exclusive words (but/except/without), *more* negative-emotion
  words, and *more* motion verbs.
- Verifiability Approach — Nahari/Vrij (via Vrij 2008): truthful accounts contain
  *more* verifiable, checkable detail (names, numbers, dates, places). High
  verifiability is therefore counter-evidence (it dampens, not raises, risk).
- Impression management / Interpersonal Deception Theory framing: dense
  self-presentational assurances ("believe me", "to tell the truth") are a
  review flag, not proof.

Thresholds are deliberately conservative and confidences deliberately low: these
are screening signals for human review, matching BIVE's product boundary.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .models import (
    Claim,
    EvidenceDirection,
    EvidenceEvent,
    Modality,
    ProvenanceRecord,
)

_WORD_RE = re.compile(r"[a-zа-яіїєґ'’]+", re.IGNORECASE)
_PROPER_RE = re.compile(r"\b[A-Z][a-zA-Zа-яіїєґ]{2,}")
_NUMERIC_RE = re.compile(r"[$£€]?\d[\d,\.]*")

FIRST_PERSON_SINGULAR = frozenset(
    {
        "i", "me", "my", "mine", "myself", "i'm", "i've", "i'd", "i'll",
        "я", "мене", "мені", "мною", "мій", "моя", "моє", "мої",
    }
)
EXCLUSIVE_WORDS = frozenset(
    {
        "but", "except", "without", "exclude", "excluding", "unless", "although",
        "however", "besides", "nor", "whereas", "aside",
        "але", "крім", "окрім", "без", "хоча", "проте", "однак", "натомість",
    }
)
NEGATIVE_EMOTION = frozenset(
    {
        "hate", "hated", "worthless", "sad", "angry", "afraid", "fear", "danger",
        "dangerous", "wrong", "smear", "smears", "crook", "crooks", "corruption",
        "corrupt", "mess", "attack", "attacked", "mistake", "mistakes", "lost",
        "loss", "threat", "guilty", "ashamed", "hurt", "enemy",
        "ненависть", "поганий", "страх", "небезпека", "помилка", "загроза",
        "зрада", "провина", "ворог",
    }
)
MOTION_VERBS = frozenset(
    {
        "go", "going", "goes", "gone", "come", "came", "coming", "walk", "walked",
        "move", "moving", "moved", "run", "ran", "carry", "carried", "drive",
        "drove", "went", "bring", "brought", "gonna", "leave", "left", "arrive",
        "йти", "іду", "прийти", "прийшов", "рухатися", "бігти", "нести", "їхати",
    }
)
IMPRESSION_MARKERS: tuple[str, ...] = (
    "believe me",
    "to tell the truth",
    "tell you the truth",
    "let me say",
    "i want you to know",
    "i can say",
    "i am proud",
    "i'm proud",
    "the fact is",
    "honest",
    "honestly",
    "integrity",
    "повірте",
    "повір мені",
    "чесно",
    "чесність",
    "правду кажучи",
    "хочу щоб ви знали",
)


@dataclass(frozen=True)
class _MarkerHit:
    feature: str
    value: str
    ratio: float
    direction: EvidenceDirection
    confidence: float
    magnitude: float
    reference: str
    interpretation: str


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]


def _ratio(count: int, total: int) -> float:
    return count / total if total else 0.0


def compute_markers(text: str) -> list[_MarkerHit]:
    """Compute the style markers that fire for ``text`` (conservative thresholds)."""
    tokens = _tokens(text)
    total = len(tokens)
    if total < 40:
        # Too little text for population-level rate features to mean anything.
        return []

    counts = {
        "fps": sum(1 for t in tokens if t in FIRST_PERSON_SINGULAR),
        "excl": sum(1 for t in tokens if t in EXCLUSIVE_WORDS),
        "neg": sum(1 for t in tokens if t in NEGATIVE_EMOTION),
        "motion": sum(1 for t in tokens if t in MOTION_VERBS),
    }
    fps_r = _ratio(counts["fps"], total)
    excl_r = _ratio(counts["excl"], total)
    neg_r = _ratio(counts["neg"], total)
    motion_r = _ratio(counts["motion"], total)

    verifiable = len(_PROPER_RE.findall(text)) + len(_NUMERIC_RE.findall(text))
    verif_r = _ratio(verifiable, total)
    impression = sum(text.lower().count(marker) for marker in IMPRESSION_MARKERS)
    impression_r = _ratio(impression, total)
    type_token_ratio = len(set(tokens)) / total  # lexical diversity

    hits: list[_MarkerHit] = []

    # Vrij (2008) cognitive approach: lying is cognitively demanding, so fabricated
    # accounts tend to be less lexically rich (more repetition, fewer distinct
    # words). Low type-token ratio on a long-enough passage is a weak load cue.
    if total >= 60 and type_token_ratio < 0.42:
        hits.append(
            _MarkerHit(
                "cognitive_load_markers",
                f"{type_token_ratio:.3f} lexical diversity (type-token ratio)",
                type_token_ratio,
                EvidenceDirection.SUPPORTS,
                0.40,
                min(0.5, (0.42 - type_token_ratio) * 6 + 0.15),
                "vrij_2008",
                "Low lexical diversity is a weak cognitive-load proxy, not deception itself.",
            )
        )

    # Newman & Pennebaker (2003): fewer first-person singular in deception.
    if fps_r < 0.030:
        hits.append(
            _MarkerHit(
                "low_first_person_singular",
                f"{fps_r:.3f} first-person-singular rate",
                fps_r,
                EvidenceDirection.SUPPORTS,
                0.42,
                min(0.5, (0.030 - fps_r) * 12),
                "newman_pennebaker_2003",
                "Low self-reference is weakly associated with distancing in the literature.",
            )
        )
    # Fewer exclusive words (but/except) — reduced cognitive complexity.
    if excl_r < 0.008:
        hits.append(
            _MarkerHit(
                "low_exclusive_words",
                f"{excl_r:.3f} exclusive-word rate",
                excl_r,
                EvidenceDirection.SUPPORTS,
                0.45,
                min(0.5, (0.008 - excl_r) * 45),
                "newman_pennebaker_2003",
                "Few exclusive words weakly track lower narrative complexity.",
            )
        )
    # More negative-emotion words.
    if neg_r > 0.018:
        hits.append(
            _MarkerHit(
                "elevated_negative_emotion",
                f"{neg_r:.3f} negative-emotion rate",
                neg_r,
                EvidenceDirection.SUPPORTS,
                0.48,
                min(0.55, (neg_r - 0.018) * 20),
                "newman_pennebaker_2003",
                "Negative-emotion density is context-sensitive and not deception per se.",
            )
        )
    # More motion verbs — keeping the story moving.
    if motion_r > 0.030:
        hits.append(
            _MarkerHit(
                "elevated_motion_verbs",
                f"{motion_r:.3f} motion-verb rate",
                motion_r,
                EvidenceDirection.SUPPORTS,
                0.40,
                min(0.5, (motion_r - 0.030) * 14),
                "newman_pennebaker_2003",
                "Motion-verb elevation is a weak stylistic cue only.",
            )
        )
    # Impression-management density — self-presentational assurances.
    if impression_r > 0.006:
        hits.append(
            _MarkerHit(
                "impression_management",
                f"{impression} self-presentational assurances",
                impression_r,
                EvidenceDirection.SUPPORTS,
                0.50,
                min(0.6, impression_r * 60),
                "ekman_friesen_1969",
                "Dense assurance framing invites verification; it is not proof of intent.",
            )
        )
    # Verifiability Approach: dense checkable detail is COUNTER-evidence.
    if verif_r > 0.060:
        hits.append(
            _MarkerHit(
                "high_verifiability",
                f"{verifiable} verifiable details ({verif_r:.3f} rate)",
                verif_r,
                EvidenceDirection.REFUTES,
                0.55,
                min(0.6, (verif_r - 0.060) * 6 + 0.25),
                "vrij_2008",
                "Abundant checkable detail is associated with truthful accounts (Verifiability Approach).",
            )
        )
    return hits


def build_style_events(claims: Sequence[Claim]) -> list[EvidenceEvent]:
    """Build transcript-level :class:`EvidenceEvent` records from style markers."""
    text = "\n".join(c.text for c in claims)
    events: list[EvidenceEvent] = []
    for hit in compute_markers(text):
        if hit.feature == "cognitive_load_markers":
            hypothesis_refs: tuple[str, ...] = ("H_COGNITIVE_LOAD_RISK",)
        elif hit.direction == EvidenceDirection.REFUTES:
            hypothesis_refs = ("H_LINGUISTIC_STYLE_RISK", "H_INCONSISTENCY_RISK")
        else:
            hypothesis_refs = ("H_LINGUISTIC_STYLE_RISK",)
        events.append(
            EvidenceEvent(
                event_id=f"event:{hit.feature}",
                source_id="transcript",
                modality=Modality.TEXT,
                feature=hit.feature,
                value=hit.value,
                confidence=round(hit.confidence, 3),
                magnitude=round(max(0.1, hit.magnitude), 3),
                direction=hit.direction,
                hypothesis_refs=hypothesis_refs,
                limitations=(
                    hit.interpretation,
                    "Population-level linguistic tendency; must never be read as individual proof.",
                ),
                provenance=ProvenanceRecord(
                    entity_id="transcript",
                    activity="linguistic_style_marker",
                    agent="bive.style_markers.compute_markers",
                    source="transcript",
                    parameters={"feature": hit.feature, "reference": hit.reference, "rate": round(hit.ratio, 5)},
                ),
            )
        )
    return events
