"""Corroboration-question generation — the operational output of COGVERITAS.

For every externally checkable claim, produce a concrete action: *which external
source would confirm or refute this?* For unverifiable opinion, say so plainly.
These questions are the product's actual value — they route a human reviewer to
external facts, not to a verdict. Never a person-level judgment.
"""

from __future__ import annotations

from .output_contract import VerifiabilityGap
from .verifiability_tagger import (
    _NUMERIC,
    _PROPER,
    _TEMPORAL,
    Claim,
    build_feature_vector,
    classify_claim_verifiability,
)


def _quote(text: str, n: int = 90) -> str:
    # Neutralize any guillemets inside the user span so the wrapper «…» stays the
    # only guillemet pair. Otherwise user-supplied » / « split the wrapper and the
    # no-verdict scan (which strips «…» spans) could either miss the whole quote
    # or falsely reject legitimate quoted evidence — e.g. a courtroom transcript
    # containing «he found him guilty». The quote is verbatim evidence; only the
    # delimiter is normalized.
    t = text.strip().replace("«", '"').replace("»", '"')
    return t if len(t) <= n else f"{t[:n]}…"


def corroboration_questions(claims: list[Claim], limit: int = 6) -> list[str]:
    """Concrete external-verification questions for the checkable claims."""
    questions: list[str] = []
    for claim in claims:
        if classify_claim_verifiability(claim) != "externally_checkable":
            continue
        entities = _PROPER.findall(claim.text)
        numbers = _NUMERIC.findall(claim.text)
        times = _TEMPORAL.findall(claim.text)
        anchors: list[str] = []
        if entities:
            anchors.append(f"named entities ({', '.join(entities[:3])})")
        if numbers:
            anchors.append(f"figures ({', '.join(numbers[:3])})")
        if times:
            anchors.append("the stated time/date")
        anchor_text = "; ".join(anchors) or "the stated specifics"
        questions.append(
            f"What independent record would confirm or refute {anchor_text} in: «{_quote(claim.text)}»?"
        )
        if len(questions) >= limit:
            break
    if not questions:
        questions.append(
            "No externally checkable detail was found — request a specific, verifiable account "
            "(who, what, when, where, with which documents) before any review conclusion."
        )
    return questions


def verifiability_gap(claims: list[Claim]) -> VerifiabilityGap:
    """Ordinal gap: elevated (few checkable claims), nominal, or insufficient."""
    features = build_feature_vector(claims)
    total = features.count_verifiable + features.count_unverifiable
    if total < 2:
        return "insufficient"
    # A low share of externally checkable claims is an elevated verification gap
    # (more of the account rests on unverifiable assertion). This is a review
    # priority, never a probability of deception.
    return "elevated" if features.verifiability_ratio < 0.34 else "nominal"


def unverifiable_notes(claims: list[Claim], limit: int = 4) -> list[str]:
    notes: list[str] = []
    for claim in claims:
        if classify_claim_verifiability(claim) == "not_externally_checkable":
            notes.append(f"unverifiable assertion — corroboration required: «{_quote(claim.text, 70)}»")
        if len(notes) >= limit:
            break
    return notes
