"""Timeline construction and inconsistency flagging (no verdict).

Two deterministic, language-aware aids for a human reviewer:

* ``build_timeline`` — order the claims that carry a resolvable time reference
  (clock time and/or an explicit date), so the account can be read chronologically.
* ``detect_conflicts`` — flag *review-worthy inconsistencies*: two claims that
  overlap heavily in content but disagree in negation polarity, or that state
  different figures for the same content. These are pointers for a human to
  check — never an assertion that a claim is false or a person is lying.
"""

from __future__ import annotations

import re

from .lang import pack_for_code
from .verifiability_tagger import Claim

_CLOCK = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_HOUR = re.compile(r"\b(?:о|в|at)\s?(\d{1,2})\b", re.IGNORECASE)


def _day_near_month(text: str, month_token: str) -> int:
    """The 1-2 digit day adjacent to the month name (before or after it), or 99 if
    none — never a distant digit like the clock hour."""
    if not month_token:
        return 99
    esc = re.escape(month_token)
    for pattern in (rf"(\d{{1,2}})\s+{esc}", rf"{esc}\s+(\d{{1,2}})"):
        m = re.search(pattern, text, re.IGNORECASE)
        if m and 1 <= int(m.group(1)) <= 31:
            return int(m.group(1))
    return 99

# Month-name stems -> month number, per language. Matched by token startswith.
_MONTHS: dict[str, dict[str, int]] = {
    "uk": {
        "січ": 1, "лют": 2, "берез": 3, "квіт": 4, "трав": 5, "черв": 6,
        "лип": 7, "серп": 8, "верес": 9, "жовт": 10, "листопад": 11, "груд": 12,
    },
    "ru": {
        "янв": 1, "февр": 2, "март": 3, "апрел": 4, "мая": 5, "май": 5, "июн": 6,
        "июл": 7, "август": 8, "сентябр": 9, "октябр": 10, "ноябр": 11, "декабр": 12,
    },
    "en": {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    },
}

# Relative day markers -> coarse offset, used only to order claims that carry no
# absolute date; kept separate from real dates so nothing is fabricated.
_RELATIVE: dict[str, dict[str, int]] = {
    "uk": {"позавчора": -2, "вчора": -1, "сьогодні": 0, "завтра": 1},
    "ru": {"позавчера": -2, "вчера": -1, "сегодня": 0, "завтра": 1},
    "en": {"yesterday": -1, "today": 0, "tomorrow": 1},
}

_NO_KEY = (99, 99, 9999)


def _time_key(claim: Claim) -> tuple[tuple[int, int, int], str, bool] | None:
    """Return (sort_key, label, resolved) if the claim carries any time reference.

    ``resolved`` is True when an absolute clock/date was found; relative-only
    references still order the claim but are flagged approximate.
    """
    text = claim.text
    lowered = [t.lower() for t in claim.tokens]
    months = _MONTHS.get(claim.lang, _MONTHS["en"])
    relative = _RELATIVE.get(claim.lang, _RELATIVE["en"])

    minutes = _NO_KEY[2]
    label_parts: list[str] = []
    resolved = False

    clock = _CLOCK.search(text)
    if clock:
        minutes = int(clock.group(1)) * 60 + int(clock.group(2))
        label_parts.append(clock.group(0))
        resolved = True
    else:
        hour = _HOUR.search(text)
        if hour and int(hour.group(1)) < 24:
            minutes = int(hour.group(1)) * 60
            label_parts.append(hour.group(0))
            resolved = True

    month = 99
    day = 99
    month_token = ""
    for tok in lowered:
        for stem, num in months.items():
            if tok.startswith(stem):
                month = num
                month_token = tok
                label_parts.append(tok)
                resolved = True
                break
        if month != 99:
            break
    if month != 99:
        # The day is the number ADJACENT to the month name ("5 січня", "March 3"),
        # not the first digit run in the sentence — which is usually the clock hour
        # ("о 9 годині 5 січня" must yield day 5, not 9).
        day = _day_near_month(text, month_token)

    rel_offset = None
    for tok in lowered:
        if tok in relative:
            rel_offset = relative[tok]
            label_parts.append(tok)
            break

    if not resolved and rel_offset is None:
        return None
    # Absolute date/clock sorts by (month, day, minutes); relative-only claims are
    # placed by a coarse offset in the month slot so they still order sensibly.
    if month == 99 and not clock and rel_offset is not None:
        key = (50 + rel_offset, 99, minutes)
    else:
        key = (month, day, minutes)
    return key, " ".join(label_parts).strip(), resolved


def build_timeline(claims: list[Claim]) -> list[dict[str, object]]:
    """Time-anchored claims, ordered. Claims without any time reference are omitted."""
    dated: list[tuple[tuple[int, int, int], dict[str, object]]] = []
    for claim in claims:
        keyed = _time_key(claim)
        if keyed is None:
            continue
        key, label, resolved = keyed
        dated.append(
            (
                key,
                {
                    "claim_id": claim.claim_id,
                    "quote": claim.text,
                    "time_label": label,
                    "resolved": resolved,
                },
            )
        )
    dated.sort(key=lambda pair: pair[0])
    return [item for _, item in dated]


# Light suffix-stripper for Ukrainian/Russian inflection (longest suffix first),
# then a length cap. Crude but enough to unify «Петру»/«Петро», «отримав»/
# «отримував» for overlap comparison — not a linguistic lemmatiser.
_SUFFIXES = (
    "увала", "ував", "ості", "ями", "ами", "ах", "ів", "ов", "ем", "ом", "их",
    "ій", "ти", "ть", "ся", "ло", "ла", "ли", "на", "но", "ні", "ий", "ая",
    "ое", "ые", "в", "л", "ю", "я", "у", "и", "і", "а", "о", "е", "ь", "й",
)


def _stem(token: str) -> str:
    t = token.lower()
    for suf in _SUFFIXES:
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            t = t[: -len(suf)]
            break
    return t[:5]


def _content_stems(claim: Claim) -> set[str]:
    pack = pack_for_code(claim.lang)
    return {
        _stem(t)
        for t in claim.tokens
        if len(t) >= 3 and t.lower() not in pack.negation and not t.isdigit()
    }


def _is_negated(claim: Claim) -> bool:
    pack = pack_for_code(claim.lang)
    return any(t.lower() in pack.negation or t.lower().endswith("n't") for t in claim.tokens)


def _overlap_coef(a: set[str], b: set[str]) -> float:
    """Overlap coefficient |A∩B|/min(|A|,|B|). Robust when one claim carries extra
    context (a date, a place) that would deflate a Jaccard score — we care whether
    the shorter claim's content is echoed by the other."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def detect_conflicts(
    claims: list[Claim], overlap: float = 0.6, limit: int = 12
) -> list[dict[str, object]]:
    """Flag review-worthy inconsistencies between claim pairs. Never a verdict."""
    conflicts: list[dict[str, object]] = []
    stems = [_content_stems(c) for c in claims]
    negated = [_is_negated(c) for c in claims]
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            a, b = claims[i], claims[j]
            if a.lang != b.lang:
                continue
            # Cross-speaker pairs are the cross-witness layer's job; here we flag
            # inconsistencies within a single account (or unattributed text).
            if a.speaker and b.speaker and a.speaker != b.speaker:
                continue
            sim = _overlap_coef(stems[i], stems[j])
            if sim < overlap:
                continue
            pack = pack_for_code(claims[i].lang)
            nums_i = set(pack.numeric.findall(claims[i].text))
            nums_j = set(pack.numeric.findall(claims[j].text))
            kind = None
            if negated[i] != negated[j]:
                kind = "negation_polarity"
            elif nums_i and nums_j and nums_i != nums_j:
                kind = "figure_mismatch"
            if kind is None:
                continue
            conflicts.append(
                {
                    "type": kind,
                    "claim_ids": [claims[i].claim_id, claims[j].claim_id],
                    "quotes": [claims[i].text, claims[j].text],
                }
            )
            if len(conflicts) >= limit:
                return conflicts
    return conflicts
