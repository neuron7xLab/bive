"""Verbal deception features grounded in the most durable evidence.

Every feature here maps to a construct with meta-analytic support, computed as an
interpretable, transparent statistic (no black box). References:

- Verifiability Approach (Nahari, Vrij & Fisher 2014; meta: Palena 2021 g~0.42-0.49,
  Verschuere 2021 d=0.49): truth-tellers give more *checkable* detail.
- Reality Monitoring (Johnson & Raye 1981; Vrij 2015): true accounts carry more
  perceptual, spatial and temporal detail; fabricated ones carry more cognitive
  operations (internally generated).
- Linguistic style (Newman, Pennebaker, Berry & Richards 2003, "Lying Words"):
  liars use fewer self/other references... (their finding), more negative emotion,
  more motion, lower cognitive complexity. Reported here as low-weight features.

These are population-level signals for human review, never a person-level verdict.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[a-z']+")
_SENT = re.compile(r"[.!?]+")
_CAP = re.compile(r"\b[A-Z][a-z]{2,}")
_NUM = re.compile(r"\$?\d[\d,.]*")
_TIME = re.compile(
    r"\b(\d{1,2}\s?(am|pm)|\d{1,2}:\d{2}|morning|noon|afternoon|evening|night|midnight|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|minutes?|hours?|days?|weeks?|nights?)\b"
)

PERCEPTUAL = {
    "saw", "see", "seen", "look", "looked", "looking", "watch", "watched", "heard",
    "hear", "sound", "sounds", "loud", "quiet", "smell", "smelled", "taste", "tasted",
    "felt", "feel", "touch", "soft", "hard", "warm", "cold", "hot", "bright", "dark",
    "color", "colour", "white", "black", "red", "blue", "green", "clean", "dirty",
    "view", "views", "spacious", "small", "large", "comfortable",
}
SPATIAL = {
    "near", "next", "across", "behind", "front", "beside", "around", "corner",
    "floor", "floors", "upstairs", "downstairs", "left", "right", "above", "below",
    "downtown", "street", "avenue", "ave", "block", "blocks", "walk", "walking",
    "distance", "located", "location", "north", "south", "east", "west", "mile",
    "miles", "minute", "away", "close", "nearby", "lobby", "elevator", "hallway",
}
COG_OPS = {
    "think", "thought", "believe", "guess", "suppose", "realize", "realized",
    "remember", "remembered", "decide", "decided", "reason", "reasons", "maybe",
    "probably", "seem", "seemed", "wonder", "expect", "expected", "assume", "opinion",
}
FIRST_SING = {"i", "i'm", "i've", "i'd", "i'll", "me", "my", "mine", "myself"}
FIRST_PLUR = {"we", "we're", "we've", "our", "ours", "us", "ourselves"}
EXCLUSIVE = {"but", "except", "without", "unless", "although", "however", "whereas", "besides"}
NEG_EMOTION = {
    "bad", "worst", "terrible", "awful", "horrible", "dirty", "rude", "disappointed",
    "disappointing", "poor", "unfriendly", "uncomfortable", "noisy", "broken", "problem",
    "problems", "complaint", "hate", "hated", "angry", "upset", "worse", "unacceptable",
}
POS_SUPERLATIVE = {
    "amazing", "wonderful", "perfect", "best", "excellent", "fantastic", "great",
    "beautiful", "incredible", "awesome", "lovely", "gorgeous", "outstanding", "superb",
    "luxurious", "magnificent", "definitely", "absolutely", "highly",
}
MOTION = {
    "go", "going", "went", "come", "came", "walk", "walked", "run", "ran", "drive",
    "drove", "arrive", "arrived", "leave", "left", "move", "moved", "get", "got", "took",
}

FEATURE_NAMES = [
    "verifiability_density",   # Verifiability Approach (higher -> more truthful)
    "perceptual_density",      # Reality Monitoring (higher -> more truthful)
    "spatial_density",         # Reality Monitoring
    "temporal_density",        # Reality Monitoring
    "cognitive_ops_density",   # RM: higher -> more internally generated (deceptive)
    "first_singular_density",  # Lying Words
    "first_plural_density",
    "exclusive_density",       # cognitive complexity (higher -> more truthful)
    "neg_emotion_density",
    "pos_superlative_density",
    "motion_density",
    "lexical_diversity",       # type-token ratio (higher -> richer, more truthful)
    "mean_sentence_len",
    "word_count",
]


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def extract(text: str) -> dict[str, float]:
    toks = _tokens(text)
    n = len(toks) or 1
    counts = {
        "perc": sum(t in PERCEPTUAL for t in toks),
        "spat": sum(t in SPATIAL for t in toks),
        "fs": sum(t in FIRST_SING for t in toks),
        "fp": sum(t in FIRST_PLUR for t in toks),
        "exc": sum(t in EXCLUSIVE for t in toks),
        "neg": sum(t in NEG_EMOTION for t in toks),
        "pos": sum(t in POS_SUPERLATIVE for t in toks),
        "mot": sum(t in MOTION for t in toks),
        "cog": sum(t in COG_OPS for t in toks),
    }
    verifiable = len(_CAP.findall(text)) + len(_NUM.findall(text))
    temporal = len(_TIME.findall(text.lower()))
    sents = [s for s in _SENT.split(text) if s.strip()]
    return {
        "verifiability_density": verifiable / n,
        "perceptual_density": counts["perc"] / n,
        "spatial_density": counts["spat"] / n,
        "temporal_density": temporal / n,
        "cognitive_ops_density": counts["cog"] / n,
        "first_singular_density": counts["fs"] / n,
        "first_plural_density": counts["fp"] / n,
        "exclusive_density": counts["exc"] / n,
        "neg_emotion_density": counts["neg"] / n,
        "pos_superlative_density": counts["pos"] / n,
        "motion_density": counts["mot"] / n,
        "lexical_diversity": len(set(toks)) / n,
        "mean_sentence_len": n / (len(sents) or 1),
        "word_count": float(n),
    }


def vectorize(text: str) -> list[float]:
    f = extract(text)
    return [f[name] for name in FEATURE_NAMES]
