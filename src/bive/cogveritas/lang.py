"""Language packs for the verifiability tagger — deterministic, per-language.

The verifiability layer answers "which claims are externally checkable?" using
language-specific anchors: proper nouns, numbers, and time/place markers. That
lexical knowledge is isolated here so the tagger stays language-agnostic and new
languages are added without touching the logic.

Supported: English (``en``), Ukrainian (``uk``), Russian (``ru``). Detection is a
transparent Cyrillic/Latin ratio with a Ukrainian-vs-Russian tie-break on
language-unique letters — no model, fully reproducible.

Nothing here judges a speaker; these are review anchors, not deception cues.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguagePack:
    """Per-language anchors for verifiability tagging."""

    code: str
    word: re.Pattern[str]
    proper: re.Pattern[str]
    numeric: re.Pattern[str]
    temporal: re.Pattern[str]
    spatial: frozenset[str]
    unverifiable: frozenset[str]
    # Stems of record-producing actions (signed, paid, called, met…). A claim that
    # names such an action is externally checkable even without a named-entity
    # anchor — the action itself leaves a verifiable record.
    actions: frozenset[str] = frozenset()
    # Negation words — for polarity-based contradiction detection (two claims that
    # overlap heavily but disagree in negation are a review-worthy inconsistency).
    negation: frozenset[str] = frozenset()
    # Capitalised function words (pronouns, deictics, conjunctions) the proper-noun
    # proxy over-captures at sentence start. Excluded so they are NOT counted as
    # named-entity anchors — otherwise "This is beautiful." reads as checkable.
    stop_names: frozenset[str] = frozenset()


# --- English -----------------------------------------------------------------

_EN = LanguagePack(
    code="en",
    word=re.compile(r"[A-Za-z']+"),
    proper=re.compile(r"\b[A-Z][a-zA-Z]{2,}"),
    numeric=re.compile(r"[$£€₴]?\d[\d,.:]*"),
    temporal=re.compile(
        r"\b(\d{1,2}\s?(?:am|pm)|\d{1,2}:\d{2}|monday|tuesday|wednesday|thursday|friday|"
        r"saturday|sunday|january|february|march|april|may|june|july|august|september|"
        r"october|november|december|yesterday|today|tomorrow|morning|afternoon|evening|"
        r"night|minutes?|hours?|days?|weeks?|months?|years?)\b",
        re.IGNORECASE,
    ),
    spatial=frozenset(
        {
            "at", "near", "across", "behind", "front", "beside", "corner", "floor",
            "upstairs", "downstairs", "left", "right", "north", "south", "east", "west",
            "street", "avenue", "road", "block", "downtown", "building", "room", "office",
            "outside", "inside", "above", "below", "next", "opposite",
        }
    ),
    unverifiable=frozenset(
        {
            "think", "believe", "feel", "felt", "guess", "suppose", "seem", "seemed",
            "opinion", "maybe", "probably", "hope", "wish", "love", "hate", "like",
            "beautiful", "amazing", "wonderful", "terrible", "awful", "nice", "great",
            "good", "bad", "perfect", "worst", "best",
        }
    ),
    actions=frozenset(
        {
            "gave", "signed", "paid", "transferred", "called", "met", "bought",
            "sold", "received", "sent", "drove", "wrote", "delivered", "arrived",
            "departed", "handed", "deposited", "withdrew",
        }
    ),
    negation=frozenset({"not", "no", "never", "none", "nobody", "nothing", "neither", "nor"}),
    stop_names=frozenset(
        {
            "the", "this", "that", "then", "there", "when", "if", "but", "so",
            "no", "yes", "also", "he", "she", "they", "it", "we", "you", "i",
            "maybe", "perhaps", "here", "now", "today", "yesterday", "tomorrow",
        }
    ),
)

# Cyrillic word/proper patterns are shared by uk and ru. A "word" is any run of
# unicode letters; a proper noun is a capitalised Cyrillic token of length >= 3.
_CYR_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_CYR_PROPER = re.compile(r"\b[А-ЯЁЄІЇҐ][а-яёєіїґ'’]{2,}")
# Numbers, optionally prefixed by a currency sign (hryvnia ₴ included).
_CYR_NUMERIC = re.compile(r"[$£€₴]?\d[\d,.:]*")

# --- Ukrainian ---------------------------------------------------------------

_UK = LanguagePack(
    code="uk",
    word=_CYR_WORD,
    proper=_CYR_PROPER,
    numeric=_CYR_NUMERIC,
    temporal=re.compile(
        r"(\d{1,2}:\d{2}|\bо\s?\d{1,2}\b|понеділок|вівторок|серед[аи]|четвер|"
        r"п['’ ]?ятниц[яі]|субот[аи]|неділ[яі]|"
        r"січн[яі]|лют(?:ого|ий)|березн[яі]|квітн[яі]|травн[яі]|червн[яі]|липн[яі]|"
        r"серпн[яі]|вересн[яі]|жовтн[яі]|листопад[аі]?|грудн[яі]|"
        r"вчора|сьогодні|завтра|позавчора|ранку|ранці|вдень|ввечері|увечері|вночі|"
        r"хвилин\w*|годин\w*|дн(?:і|я|ів)|тижд\w*|тижн\w*|місяц\w*|рок\w*|рік)\b",
        re.IGNORECASE,
    ),
    spatial=frozenset(
        {
            "біля", "поруч", "навпроти", "перед", "позаду", "ріг", "розі", "поверх",
            "вгорі", "внизу", "ліворуч", "праворуч", "північ", "південь", "схід",
            "захід", "вулиця", "вулиці", "проспект", "площа", "площі", "будинок",
            "будинку", "кімната", "кімнаті", "офіс", "офісі", "під'їзд", "підʼїзд",
            "район", "районі", "місто", "місті", "село", "селі", "квартира",
            "квартирі", "зовні", "всередині", "адреса", "адресою",
        }
    ),
    unverifiable=frozenset(
        {
            "думаю", "вважаю", "здається", "здавалося", "мабуть", "напевно",
            "можливо", "гадаю", "припускаю", "сподіваюся", "начебто", "ніби",
            "нібито", "відчуваю", "відчув", "люблю", "ненавиджу", "подобається",
            "гарний", "гарно", "чудовий", "чудово", "жахливий", "жахливо",
            "поганий", "погано", "найкращий", "найгірший", "красиво", "красивий",
        }
    ),
    actions=frozenset(
        {
            "переда", "підписа", "оплат", "заплат", "переказ", "дзвон", "подзвон",
            "зателефон", "зустрі", "купив", "купила", "продав", "отрима", "надісла",
            "надсила", "поїха", "приїха", "виїха", "написа", "вручив", "вніс",
            "зняв", "перерахув",
        }
    ),
    negation=frozenset(
        {
            "не", "ні", "ніколи", "немає", "нема", "жодного", "жодної", "жодних",
            "жодним", "жоден", "ніхто", "нічого", "ніде", "ніяк", "аніяк",
        }
    ),
    stop_names=frozenset(
        {
            "він", "вона", "вони", "воно", "це", "цей", "ця", "потім", "тоді",
            "тут", "там", "коли", "якщо", "проте", "однак", "але", "так", "ні",
            "що", "як", "де", "бо", "адже", "отже", "тобто", "також", "ще", "вже",
            "мене", "мені", "нього", "неї", "їх", "ми", "ти", "ви", "я",
        }
    ),
)

# --- Russian -----------------------------------------------------------------

_RU = LanguagePack(
    code="ru",
    word=_CYR_WORD,
    proper=_CYR_PROPER,
    numeric=_CYR_NUMERIC,
    temporal=re.compile(
        r"(\d{1,2}:\d{2}|\bв\s?\d{1,2}\s?(?:час\w*)?\b|понедельник|вторник|сред[аы]|"
        r"четверг|пятниц[аы]|суббот[аы]|воскресень\w*|"
        r"январ\w*|феврал\w*|март\w*|апрел\w*|ма[йя]|июн\w*|июл\w*|август\w*|"
        r"сентябр\w*|октябр\w*|ноябр\w*|декабр\w*|"
        r"вчера|сегодня|завтра|позавчера|утром|утра|днём|днем|вечером|ночью|"
        r"минут\w*|час\w*|дн(?:я|ей|и)|недел\w*|месяц\w*|год\w*|лет)\b",
        re.IGNORECASE,
    ),
    spatial=frozenset(
        {
            "возле", "около", "рядом", "напротив", "перед", "позади", "угол",
            "углу", "этаж", "этаже", "наверху", "внизу", "слева", "справа",
            "север", "юг", "восток", "запад", "улица", "улице", "проспект",
            "площадь", "площади", "дом", "дома", "доме", "комната", "комнате",
            "офис", "офисе", "подъезд", "район", "районе", "город", "городе",
            "село", "селе", "квартира", "квартире", "снаружи", "внутри", "адрес",
            "адресу",
        }
    ),
    unverifiable=frozenset(
        {
            "думаю", "считаю", "кажется", "казалось", "наверное", "возможно",
            "полагаю", "предполагаю", "надеюсь", "вроде", "будто", "якобы",
            "чувствую", "почувствовал", "люблю", "ненавижу", "нравится",
            "красивый", "красиво", "прекрасный", "ужасный", "ужасно", "плохой",
            "плохо", "лучший", "худший", "замечательный",
        }
    ),
    actions=frozenset(
        {
            "переда", "подписа", "оплат", "заплат", "перевёл", "перевел", "звон",
            "позвон", "встрет", "купил", "продал", "получил", "отправ", "поеха",
            "приеха", "выеха", "написа", "вручил", "внёс", "внес", "снял", "перечисл",
        }
    ),
    negation=frozenset(
        {"не", "нет", "никогда", "нету", "ни", "никто", "ничего", "нигде", "нисколько"}
    ),
    stop_names=frozenset(
        {
            "он", "она", "они", "оно", "это", "этот", "эта", "потом", "тогда",
            "тут", "там", "когда", "если", "однако", "но", "так", "нет", "что",
            "как", "где", "потому", "итак", "также", "ещё", "уже", "меня", "мне",
            "него", "неё", "их", "мы", "ты", "вы", "я",
        }
    ),
)

_PACKS: dict[str, LanguagePack] = {"en": _EN, "uk": _UK, "ru": _RU}

# Letters unique to each Cyrillic orthography, used to break the uk/ru tie.
_UK_ONLY = frozenset("іїєґІЇЄҐ")
_RU_ONLY = frozenset("ыэъёЫЭЪЁ")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")  # full Cyrillic block U+0400–U+04FF
_LATIN = re.compile(r"[A-Za-z]")

# Function-word tie-break for Cyrillic text that carries no language-unique
# letters (common in short statements). High-frequency words that differ between
# the orthographies; a few hits reliably separate the two.
_UK_WORDS = frozenset(
    {
        "він", "вона", "вони", "це", "був", "була", "було", "біля", "вулиця",
        "вулиці", "будинок", "будинку", "та", "що", "де", "коли", "мене", "мені",
        "гривень", "гривні", "передав", "поїхали", "зустрів", "потім", "адже",
    }
)
_RU_WORDS = frozenset(
    {
        "он", "она", "они", "это", "был", "была", "было", "возле", "около",
        "улица", "улице", "дом", "дома", "доме", "что", "где", "когда", "меня",
        "мне", "рублей", "долларов", "передал", "поехали", "встретил", "потом", "ведь",
    }
)
_WORDS = re.compile(r"[^\W\d_]+", re.UNICODE)


def detect_language(text: str) -> str:
    """Return ``en``/``uk``/``ru`` from script ratio, then language-unique letters,
    then function words.

    Transparent and reproducible: majority script decides Latin vs Cyrillic; among
    Cyrillic, Ukrainian-unique letters (і, ї, є, ґ) outrank Russian-unique ones
    (ы, э, ъ, ё); when neither appears, high-frequency function words break the
    tie. Empty input and Latin-majority default to English.
    """
    if not text:
        return "en"
    cyr = len(_CYRILLIC.findall(text))
    lat = len(_LATIN.findall(text))
    if cyr <= lat:
        return "en"
    uk_hits = sum(ch in _UK_ONLY for ch in text)
    ru_hits = sum(ch in _RU_ONLY for ch in text)
    if uk_hits != ru_hits:
        return "uk" if uk_hits > ru_hits else "ru"
    # No distinguishing letters — fall back to function-word frequency.
    tokens = [t.lower() for t in _WORDS.findall(text)]
    uk_w = sum(t in _UK_WORDS for t in tokens)
    ru_w = sum(t in _RU_WORDS for t in tokens)
    if ru_w > uk_w:
        return "ru"
    # Ties (including no marker hits) default to Ukrainian for this
    # Ukrainian-facing product; the anchor sets overlap heavily anyway.
    return "uk"


def pack_for_code(code: str) -> LanguagePack:
    return _PACKS.get(code, _EN)


def pack_for_text(text: str) -> LanguagePack:
    return pack_for_code(detect_language(text))
