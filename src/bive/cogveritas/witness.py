"""Cross-witness analysis — compare what different speakers said (no verdict).

An analyst's core question with multiple statements: where do witnesses *agree*
(mutual corroboration strengthens a checkable fact) and where do they *disagree*
(a contradiction to resolve)? This parses speaker-attributed statements and pairs
claims across different speakers.

Agreement here means "two independent accounts assert the same checkable detail",
not "this is true". Disagreement means "these accounts conflict — resolve it",
not "someone lied". The no-verdict invariant holds.
"""

from __future__ import annotations

import re

from .lang import detect_language, pack_for_code
from .timeline import _content_stems, _is_negated, _overlap_coef
from .verifiability_tagger import (
    Claim,
    _cid,
    classify_claim_verifiability,
    segment_claims,
    segment_sentences,
)

# "Name: utterance" — a speaker label up to 40 chars, then the statement. Common
# in transcripts and interrogation records. Avoids matching "14:30" style times.
_SPEAKER_LINE = re.compile(r"^\s*([^:\n]{1,40}?):\s+(.+)$")


def parse_statements(text: str) -> list[tuple[str, str]]:
    """Split into (speaker, utterance). Lines without a speaker label attach to the
    current speaker; text with no labels at all is one anonymous speaker."""
    statements: list[tuple[str, str]] = []
    current = ""
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = _SPEAKER_LINE.match(line)
        if m and not m.group(1)[0].isdigit():
            current = m.group(1).strip()
            statements.append((current, m.group(2).strip()))
        else:
            statements.append((current, line))
    return statements


def analyze_by_speaker(text: str) -> list[Claim]:
    """Claims tagged with their speaker (and detected language)."""
    lang = detect_language(text)
    pack = pack_for_code(lang)
    claims: list[Claim] = []
    for idx, (speaker, utterance) in enumerate(parse_statements(text)):
        for sent in segment_sentences(utterance):
            for base in segment_claims(sent, pack):
                # Re-key so claims from different speakers never collide on id.
                claims.append(
                    Claim(_cid(f"{speaker}:{idx}:{sent}", idx), base.text, base.tokens, pack.code, speaker)
                )
    return claims


def distinct_speakers(claims: list[Claim]) -> list[str]:
    seen: list[str] = []
    for c in claims:
        if c.speaker and c.speaker not in seen:
            seen.append(c.speaker)
    return seen


def cross_witness(
    claims: list[Claim], overlap: float = 0.6, limit: int = 16
) -> list[dict[str, object]]:
    """Pair claims from *different* speakers: contradictions and corroborations."""
    items: list[dict[str, object]] = []
    stems = [_content_stems(c) for c in claims]
    negated = [_is_negated(c) for c in claims]
    checkable = [classify_claim_verifiability(c) == "externally_checkable" for c in claims]
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            a, b = claims[i], claims[j]
            if a.lang != b.lang or not a.speaker or not b.speaker or a.speaker == b.speaker:
                continue
            if _overlap_coef(stems[i], stems[j]) < overlap:
                continue
            pack = pack_for_code(a.lang)
            nums_a = set(pack.numeric.findall(a.text))
            nums_b = set(pack.numeric.findall(b.text))
            if negated[i] != negated[j] or nums_a and nums_b and nums_a != nums_b:
                kind = "cross_contradiction"
            elif checkable[i] and checkable[j]:
                # Same polarity, overlapping, both checkable -> independent accounts
                # corroborate the same detail. Stronger than a single source.
                kind = "cross_corroboration"
            else:
                continue
            items.append(
                {
                    "type": kind,
                    "speakers": [a.speaker, b.speaker],
                    "quotes": [a.text, b.text],
                }
            )
            if len(items) >= limit:
                return items
    return items
