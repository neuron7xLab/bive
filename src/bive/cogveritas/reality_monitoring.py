"""Reality Monitoring criteria — a per-claim detail profile (no verdict).

Johnson & Raye's Reality Monitoring framework observes that externally-derived
accounts tend to carry more perceptual, spatial, temporal and contextual detail,
while internally-generated ones carry more cognitive-operation markers. Here that
is surfaced as a **detail-richness profile** per claim — which criteria are
present — explicitly NOT a truth score.

The empirical validation (docs/EMPIRICAL_VALIDATION.md) shows RM detail does not
reliably separate truth from deception in real high-stakes settings, so this is a
review aid: richer, more concrete detail is *easier to check*, not more likely
true. Presented as ordinal flags, never a probability.
"""

from __future__ import annotations

from .lang import pack_for_code
from .verifiability_tagger import Claim

# Perceptual/sensory stems per language (a Reality Monitoring criterion).
_PERCEPTUAL: dict[str, tuple[str, ...]] = {
    "uk": ("бачи", "побач", "чув", "чула", "почу", "відчу", "запах", "звук", "колір",
           "кольор", "голос", "темн", "світл", "холодн", "тепл", "гучн", "смак", "дотик"),
    "ru": ("виде", "увиде", "слыша", "услыша", "почувств", "запах", "звук", "цвет",
           "голос", "темн", "свет", "холодн", "тепл", "громк", "вкус", "прикоснов"),
    "en": ("saw", "seen", "heard", "felt", "smell", "tast", "colour", "color", "sound",
           "noise", "voice", "dark", "light", "cold", "warm", "loud", "touch"),
}


def _has_perceptual(claim: Claim) -> bool:
    stems = _PERCEPTUAL.get(claim.lang, _PERCEPTUAL["en"])
    return any(t.lower().startswith(stem) for t in claim.tokens for stem in stems)


def rm_profiles(claims: list[Claim], limit: int = 12) -> list[dict[str, object]]:
    """Per-claim Reality Monitoring detail profile. A review aid, never a verdict."""
    out: list[dict[str, object]] = []
    for claim in claims:
        pack = pack_for_code(claim.lang)
        lowered = [t.lower() for t in claim.tokens]
        temporal = bool(pack.temporal.search(claim.text))
        spatial = any(t in pack.spatial for t in lowered)
        quantitative = bool(pack.numeric.findall(claim.text))
        perceptual = _has_perceptual(claim)
        cognitive_operations = any(t in pack.unverifiable for t in lowered)
        detail_count = sum((temporal, spatial, quantitative, perceptual))
        # Only surface claims that carry at least one signal worth noting.
        if detail_count == 0 and not cognitive_operations:
            continue
        out.append(
            {
                "claim_id": claim.claim_id,
                "temporal": temporal,
                "spatial": spatial,
                "perceptual": perceptual,
                "quantitative": quantitative,
                "cognitive_operations": cognitive_operations,
                "detail_count": detail_count,
            }
        )
        if len(out) >= limit:
            break
    return out
