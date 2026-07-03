"""Case entity index — cluster and dedupe named-entity mentions (no verdict).

An analyst needs a map of *who and what appears, in what forms, and where*. This
clusters proper-noun mentions across all claims by a light morphological stem, so
inflected surface forms of one name (Петро / Петра / Петру / Коваленка) collapse
to a single entity with its mention count and the claims it appears in.

It is an index, not a judgment: it says a name occurs, never anything about the
truthfulness of the person or the claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .lang import pack_for_code
from .timeline import _stem
from .verifiability_tagger import Claim


@dataclass
class _Cluster:
    forms: set[str] = field(default_factory=set)
    claim_ids: list[str] = field(default_factory=list)
    count: int = 0

# Capitalised function words that the proper-noun proxy over-captures at sentence
# start — pronouns, conjunctions, deictics. Excluded so they are not "entities".
_STOP_NAMES: dict[str, frozenset[str]] = {
    "uk": frozenset(
        {
            "він", "вона", "вони", "воно", "це", "цей", "ця", "потім", "тоді",
            "тут", "там", "коли", "якщо", "проте", "однак", "але", "так", "ні",
            "що", "як", "де", "бо", "адже", "отже", "тобто", "також", "ще", "вже",
            "мене", "мені", "нього", "неї", "їх", "ми", "ти", "ви", "я",
        }
    ),
    "ru": frozenset(
        {
            "он", "она", "они", "оно", "это", "этот", "эта", "потом", "тогда",
            "тут", "там", "когда", "если", "однако", "но", "так", "нет", "что",
            "как", "где", "потому", "итак", "также", "ещё", "уже", "меня", "мне",
            "него", "неё", "их", "мы", "ты", "вы", "я",
        }
    ),
    "en": frozenset(
        {
            "the", "this", "that", "then", "there", "when", "if", "but", "so",
            "no", "yes", "also", "he", "she", "they", "it", "we", "you", "i",
        }
    ),
}


def extract_entities(claims: list[Claim], limit: int = 40) -> list[dict[str, object]]:
    """Cluster proper-noun mentions into canonical entities with a mention index."""
    clusters: dict[str, _Cluster] = {}
    for claim in claims:
        pack = pack_for_code(claim.lang)
        stop = _STOP_NAMES.get(claim.lang, _STOP_NAMES["en"])
        for mention in pack.proper.findall(claim.text):
            if mention.lower() in stop:
                continue
            cluster = clusters.setdefault(f"{claim.lang}:{_stem(mention)}", _Cluster())
            cluster.forms.add(mention)
            cluster.count += 1
            if claim.claim_id not in cluster.claim_ids:
                cluster.claim_ids.append(claim.claim_id)

    def _canonical(c: _Cluster) -> str:
        # Longest surface form (most informative); ties broken alphabetically.
        return max(sorted(c.forms), key=len)

    # Most-mentioned first; stable by canonical for equal counts.
    ordered = sorted(clusters.values(), key=lambda c: (-c.count, _canonical(c)))
    return [
        {
            "canonical": _canonical(c),
            "forms": sorted(c.forms),
            "count": c.count,
            "claim_ids": c.claim_ids,
        }
        for c in ordered[:limit]
    ]
