"""Corroboration worklist — route each checkable claim to concrete record types.

The analyst's real work product: not "is this true?" but "to check this claim,
which external record do you pull?" For each externally checkable claim this maps
its content to concrete record sources (telecom billing, CCTV, bank statements,
border/transit records, documents, vehicle records). Deterministic keyword/anchor
routing, language-aware, phrased in the reviewer's language.

This suggests *where to look*. It never asserts a claim is false or a person is
lying — the routing is a research aid, not a judgment.
"""

from __future__ import annotations

from .lang import pack_for_code
from .verifiability_tagger import Claim, classify_claim_verifiability

# Record-type labels per language. Keys are language-independent identifiers.
_LABELS: dict[str, dict[str, str]] = {
    "uk": {
        "telecom": "білінг оператора / логи месенджера",
        "cctv": "камери відеоспостереження / геолокація пристрою",
        "financial": "банківська виписка / касові документи",
        "border_transit": "прикордонні записи / транспортні квитки",
        "third_party": "свідчення третьої особи / записи відвідувань",
        "document": "оригінал документа / реєстр",
        "vehicle": "фіксація ДТЗ / записи поліції",
        "generic": "документальне підтвердження зазначених деталей",
    },
    "ru": {
        "telecom": "биллинг оператора / логи мессенджера",
        "cctv": "камеры видеонаблюдения / геолокация устройства",
        "financial": "банковская выписка / кассовые документы",
        "border_transit": "пограничные записи / транспортные билеты",
        "third_party": "показания третьего лица / записи посещений",
        "document": "оригинал документа / реестр",
        "vehicle": "фиксация ТС / записи полиции",
        "generic": "документальное подтверждение указанных деталей",
    },
    "en": {
        "telecom": "carrier call detail records / messenger logs",
        "cctv": "CCTV footage / device geolocation",
        "financial": "bank statement / cash records",
        "border_transit": "border-crossing records / transit tickets",
        "third_party": "third-party testimony / visitor logs",
        "document": "original document / registry",
        "vehicle": "traffic-camera records / police records",
        "generic": "documentary confirmation of the stated specifics",
    },
}

# Trigger stems per language: a claim token starting with any stem routes to the
# record type. Stems (not full words) absorb Ukrainian/Russian inflection.
_TRIGGERS: dict[str, dict[str, tuple[str, ...]]] = {
    "uk": {
        "telecom": ("телефон", "дзвон", "подзвон", "зателефон", "повідомл", "смс", "месендж", "вайбер", "телеграм", "написа", "дзвін"),
        "financial": ("гривен", "гривн", "грн", "долар", "євро", "переказ", "картк", "готівк", "заплат", "оплат", "кошт", "грош", "рахунок"),
        "border_transit": ("кордон", "виїха", "в'їха", "потяг", "поїзд", "літак", "рейс", "автобус", "квиток", "квитк", "митниц"),
        "third_party": ("зустрі", "бачив", "бачила", "свідок", "присутн", "разом", "супровод"),
        "document": ("договір", "договор", "підписа", "документ", "довідк", "акт", "розписк", "заяв", "накладн"),
        "vehicle": ("автомобіл", "машин", "держномер", "номерн", "авто"),
    },
    "ru": {
        "telecom": ("телефон", "звон", "позвон", "сообщен", "смс", "мессендж", "вайбер", "телеграм", "написа", "звонок"),
        "financial": ("рубл", "долар", "доллар", "евро", "перевод", "картеч", "картк", "наличн", "заплат", "оплат", "средств", "деньг", "счёт", "счет"),
        "border_transit": ("границ", "выеха", "въеха", "поезд", "самолёт", "самолет", "рейс", "автобус", "билет", "таможн"),
        "third_party": ("встрет", "видел", "видела", "свидетел", "присутств", "вместе", "сопровожд"),
        "document": ("договор", "подписа", "документ", "справк", "акт", "расписк", "заявлен", "накладн"),
        "vehicle": ("автомобил", "машин", "госномер", "номерн", "авто"),
    },
    "en": {
        "telecom": ("phone", "call", "called", "message", "sms", "messenger", "texted", "dialed"),
        "financial": ("dollar", "euro", "hryvnia", "payment", "paid", "card", "cash", "transfer", "account", "money"),
        "border_transit": ("border", "crossed", "flight", "train", "bus", "ticket", "customs", "departed"),
        "third_party": ("met", "saw", "witness", "present", "together", "accompanied"),
        "document": ("contract", "signed", "document", "certificate", "receipt", "statement", "invoice"),
        "vehicle": ("car", "vehicle", "automobile", "plate", "license"),
    },
}


def _labels(lang: str) -> dict[str, str]:
    return _LABELS.get(lang, _LABELS["en"])


def _match_record_types(claim: Claim) -> list[str]:
    """Language-independent record-type keys a claim routes to, ordered stably."""
    pack = pack_for_code(claim.lang)
    triggers = _TRIGGERS.get(claim.lang, _TRIGGERS["en"])
    tokens = [t.lower() for t in claim.tokens]
    matched: set[str] = set()
    for rtype, stems in triggers.items():
        if any(tok.startswith(stem) for tok in tokens for stem in stems):
            matched.add(rtype)
    # Place + time together → footage/geolocation is the canonical corroborator.
    has_place = any(t in pack.spatial for t in tokens)
    has_time = bool(pack.temporal.search(claim.text))
    if has_place and has_time:
        matched.add("cctv")
    # A checkable claim with no specific route still needs documentary backing.
    if not matched:
        matched.add("generic")
    order = ("telecom", "cctv", "financial", "border_transit", "vehicle", "third_party", "document", "generic")
    return [r for r in order if r in matched]


def corroboration_worklist(claims: list[Claim], limit: int = 12) -> list[dict[str, object]]:
    """One worklist item per externally checkable claim: the claim and the concrete
    record types that would confirm or refute it. Never a verdict."""
    items: list[dict[str, object]] = []
    for claim in claims:
        if classify_claim_verifiability(claim) != "externally_checkable":
            continue
        labels = _labels(claim.lang)
        record_types = [labels[k] for k in _match_record_types(claim)]
        items.append(
            {
                "claim_id": claim.claim_id,
                "quote": claim.text,
                "record_types": record_types,
            }
        )
        if len(items) >= limit:
            break
    return items
