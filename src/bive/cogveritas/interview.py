"""Interview question generation — elicit checkable detail (no verdict).

Grounded in the Verifiability Approach (Nahari, Vrij & Fisher) and Strategic Use
of Evidence (Granhag & Hartwig): a truthful account *can* supply checkable detail,
so the productive move is to invite more of it — not to judge. For each claim this
proposes a targeted follow-up the interviewer could ask to close a verifiability
gap (missing time, place, participants, or documents).

These are questions for the *interviewer to ask the person*, distinct from the
corroboration worklist (which tells the investigator which record to pull). Never
a judgment about the person or the claim.
"""

from __future__ import annotations

from .lang import pack_for_code
from .verifiability_tagger import Claim, classify_claim_verifiability

_TPL: dict[str, dict[str, str]] = {
    "uk": {
        "elicit": "Попросіть конкретні перевірювані деталі (хто був присутній, точний час, місце, "
        "які документи) щодо: {quote}",
        "time": "Уточніть точний час/дату щодо: {quote}",
        "place": "Уточніть точне місце (адреса, орієнтир) щодо: {quote}",
        "who": "Уточніть, хто ще був присутній і може підтвердити: {quote}",
        "r_verifiability": "Підхід перевірюваності: запросити деталі, що піддаються зовнішній перевірці.",
        "r_detail": "Заповнити відсутній якір (час/місце/учасники) для перевірюваності.",
    },
    "ru": {
        "elicit": "Запросите конкретные проверяемые детали (кто присутствовал, точное время, место, "
        "какие документы) относительно: {quote}",
        "time": "Уточните точное время/дату относительно: {quote}",
        "place": "Уточните точное место (адрес, ориентир) относительно: {quote}",
        "who": "Уточните, кто ещё присутствовал и может подтвердить: {quote}",
        "r_verifiability": "Подход проверяемости: запросить внешне проверяемые детали.",
        "r_detail": "Заполнить недостающий якорь (время/место/участники) для проверяемости.",
    },
    "en": {
        "elicit": "Ask for specific verifiable details (who was present, exact time, place, which "
        "documents) regarding: {quote}",
        "time": "Ask for the exact time/date regarding: {quote}",
        "place": "Ask for the precise place (address, landmark) regarding: {quote}",
        "who": "Ask who else was present and could confirm: {quote}",
        "r_verifiability": "Verifiability Approach: invite externally checkable detail.",
        "r_detail": "Fill a missing anchor (time/place/participants) to make it checkable.",
    },
}


def _tpl(lang: str) -> dict[str, str]:
    return _TPL.get(lang, _TPL["en"])


def _quote(text: str, n: int = 80) -> str:
    t = text.strip().replace("«", '"').replace("»", '"')
    clipped = t if len(t) <= n else f"{t[:n]}…"
    return f"«{clipped}»"


def interview_questions(claims: list[Claim], limit: int = 8) -> list[dict[str, object]]:
    """Targeted follow-ups to elicit checkable detail, per claim. Never a verdict."""
    out: list[dict[str, object]] = []
    for claim in claims:
        pack = pack_for_code(claim.lang)
        tpl = _tpl(claim.lang)
        label = classify_claim_verifiability(claim)
        has_time = bool(pack.temporal.search(claim.text))
        has_place = any(t.lower() in pack.spatial for t in claim.tokens)
        has_entity = bool(pack.proper.findall(claim.text))
        if label == "not_externally_checkable":
            question, rationale = tpl["elicit"].format(quote=_quote(claim.text)), tpl["r_verifiability"]
        elif not has_time:
            question, rationale = tpl["time"].format(quote=_quote(claim.text)), tpl["r_detail"]
        elif not has_place:
            question, rationale = tpl["place"].format(quote=_quote(claim.text)), tpl["r_detail"]
        elif not has_entity:
            question, rationale = tpl["who"].format(quote=_quote(claim.text)), tpl["r_detail"]
        else:
            continue  # already time + place + participants — well anchored
        out.append({"claim_id": claim.claim_id, "question": question, "rationale": rationale})
        if len(out) >= limit:
            break
    return out
