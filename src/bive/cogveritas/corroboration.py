"""Corroboration-question generation — the operational output of COGVERITAS.

For every externally checkable claim, produce a concrete action: *which external
source would confirm or refute this?* For unverifiable opinion, say so plainly.
These questions are the product's actual value — they route a human reviewer to
external facts, not to a verdict. Never a person-level judgment.

Phrasing is language-specific (English, Ukrainian, Russian) so the output speaks
the reviewer's language; the logic is identical across languages.
"""

from __future__ import annotations

from .lang import pack_for_code
from .output_contract import VerifiabilityGap
from .verifiability_tagger import Claim, build_feature_vector, classify_claim_verifiability

# Per-language phrasing. Same structure everywhere; only the words change.
_TPL: dict[str, dict[str, str]] = {
    "en": {
        "question": "What independent record would confirm or refute {anchors} in: {quote}?",
        "entities": "named entities ({v})",
        "figures": "figures ({v})",
        "time": "the stated time/date",
        "specifics": "the stated specifics",
        "sep": "; ",
        "none": (
            "No externally checkable detail was found — request a specific, verifiable "
            "account (who, what, when, where, with which documents) before any review conclusion."
        ),
        "unverifiable": "unverifiable assertion — corroboration required: {quote}",
    },
    "uk": {
        "question": "Який незалежний запис підтвердить або спростує {anchors} у: {quote}?",
        "entities": "згадані сутності ({v})",
        "figures": "числа/суми ({v})",
        "time": "зазначені час/дату",
        "specifics": "зазначені деталі",
        "sep": "; ",
        "none": (
            "Зовнішньо перевірюваних деталей не виявлено — запитайте конкретний "
            "перевірюваний виклад (хто, що, коли, де, якими документами) до будь-яких висновків."
        ),
        "unverifiable": "голослівне твердження — потрібна корроборація: {quote}",
    },
    "ru": {
        "question": "Какая независимая запись подтвердит или опровергнет {anchors} в: {quote}?",
        "entities": "упомянутые сущности ({v})",
        "figures": "числа/суммы ({v})",
        "time": "указанные время/дату",
        "specifics": "указанные детали",
        "sep": "; ",
        "none": (
            "Внешне проверяемых деталей не найдено — запросите конкретное "
            "проверяемое изложение (кто, что, когда, где, какими документами) до любых выводов."
        ),
        "unverifiable": "голословное утверждение — требуется корроборация: {quote}",
    },
}


def _tpl(lang: str) -> dict[str, str]:
    return _TPL.get(lang, _TPL["en"])


def _evidence(text: str) -> str:
    """Wrap user-derived text as quoted evidence: «…» with inner guillemets
    neutralized so the wrapper is the only guillemet pair.

    Every fragment lifted from the user's account (the claim quote *and* the
    extracted entity anchors) is system output but *not* the system's judgment.
    The no-verdict scan strips «…» spans before checking for forbidden judgment
    words, so any user fragment must live inside exactly one such span. If a
    fragment sat unwrapped — e.g. an entity named "Guilty" in the anchor list —
    or user-supplied » / « split the wrapper, the scan would falsely reject
    legitimate evidence (a courtroom transcript naming a "Guilty" or quoting
    «he found him guilty»). Only the delimiter is normalized; the text is verbatim.
    """
    return "«" + text.replace("«", '"').replace("»", '"') + "»"


def _quote(text: str, n: int = 90) -> str:
    t = text.strip()
    clipped = t if len(t) <= n else f"{t[:n]}…"
    return _evidence(clipped)


def _doc_lang(claims: list[Claim]) -> str:
    return claims[0].lang if claims else "en"


def corroboration_questions(claims: list[Claim], limit: int = 6) -> list[str]:
    """Concrete external-verification questions for the checkable claims."""
    questions: list[str] = []
    for claim in claims:
        if classify_claim_verifiability(claim) != "externally_checkable":
            continue
        pack = pack_for_code(claim.lang)
        tpl = _tpl(claim.lang)
        entities = pack.proper.findall(claim.text)
        numbers = pack.numeric.findall(claim.text)
        times = pack.temporal.findall(claim.text)
        anchors: list[str] = []
        if entities:
            # Entity names are user-derived; wrap them as evidence so a name like
            # "Guilty" cannot leak into the (unstripped) system framing.
            anchors.append(tpl["entities"].format(v=_evidence(", ".join(entities[:3]))))
        if numbers:
            anchors.append(tpl["figures"].format(v=", ".join(numbers[:3])))
        if times:
            anchors.append(tpl["time"])
        anchor_text = tpl["sep"].join(anchors) or tpl["specifics"]
        questions.append(
            tpl["question"].format(anchors=anchor_text, quote=_quote(claim.text))
        )
        if len(questions) >= limit:
            break
    if not questions:
        questions.append(_tpl(_doc_lang(claims))["none"])
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
            notes.append(_tpl(claim.lang)["unverifiable"].format(quote=_quote(claim.text, 70)))
        if len(notes) >= limit:
            break
    return notes
