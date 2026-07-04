"""Language packs for the verifiability tagger — deterministic, per-language.

The verifiability layer answers "which claims are externally checkable?" using
language-specific anchors: proper nouns, numbers, and time/place markers. That
lexical knowledge is isolated here so the tagger stays language-agnostic and new
languages are added without touching the logic.

Supported: English (``en``), Ukrainian (``uk``), Russian (``ru``). Detection is a
Cyrillic/Latin script ratio, a Ukrainian-vs-Russian tie-break on language-unique
letters, and a deterministic char-3-gram naive-Bayes model for the remaining short
Cyrillic text. Pure counts — fully reproducible, no randomness, no runtime deps.

Nothing here judges a speaker; these are review anchors, not deception cues.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path


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
# Keep internal apostrophes (під'їзд, п'ять) inside the token — the apostrophe is a
# letter-joiner in Ukrainian, not a boundary, so splitting it makes apostrophe-bearing
# anchors (e.g. the spatial set's "під'їзд") unreachable by token membership.
_CYR_WORD = re.compile(r"[^\W\d_]+(?:['’ʼ][^\W\d_]+)*", re.UNICODE)
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
            # sequence / time / frequency adverbs the proper-noun proxy captures at
            # sentence start — never named entities.
            "пізніше", "раніше", "спочатку", "згодом", "невдовзі", "нещодавно",
            "одразу", "врешті", "зрештою", "тепер", "зараз", "сьогодні", "вчора",
            "завтра", "знову", "часто", "іноді", "інколи", "завжди", "ніколи",
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
            # sequence / time / frequency adverbs the proper-noun proxy captures at
            # sentence start — never named entities.
            "позже", "раньше", "сначала", "вскоре", "недавно", "сразу", "наконец",
            "теперь", "сейчас", "сегодня", "вчера", "завтра", "снова", "часто",
            "иногда", "всегда", "никогда",
        }
    ),
)

_PACKS: dict[str, LanguagePack] = {"en": _EN, "uk": _UK, "ru": _RU}

# Letters unique to each Cyrillic orthography, used to break the uk/ru tie.
_UK_ONLY = frozenset("іїєґІЇЄҐ")
_RU_ONLY = frozenset("ыэъёЫЭЪЁ")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")  # full Cyrillic block U+0400–U+04FF
_LATIN = re.compile(r"[A-Za-z]")

# Character-3-gram naive-Bayes language-ID model (uk/ru/en), trained on Tatoeba
# (CC BY 2.0 FR), disjoint from the validation corpora. Replaces the function-word /
# masculine-past heuristic for Cyrillic text with no orthography-unique letter — the
# case that previously mis-routed short Russian to Ukrainian (measured ru 0.77 -> 0.98
# held-out). Pure counts: deterministic, dependency-free, order-independent scoring.
_LID_MODEL_PATH = Path(__file__).with_name("lid_model.json")


@dataclass(frozen=True)
class _LidModel:
    n: int
    log_denom: dict[str, float]  # log(total_L + V) per language
    profiles: dict[str, dict[str, int]]


def _load_lid_model() -> _LidModel:
    raw = json.loads(_LID_MODEL_PATH.read_text(encoding="utf-8"))
    vocab = int(raw["vocab_size"])
    totals: dict[str, int] = raw["totals"]
    log_denom = {lang: math.log(totals[lang] + vocab) for lang in totals}
    return _LidModel(n=int(raw["n"]), log_denom=log_denom, profiles=raw["profiles"])


_LID = _load_lid_model()


def _lid_grams(text: str) -> list[str]:
    """Lowercase, collapse non-letters to single spaces, pad, and emit char n-grams."""
    out: list[str] = []
    prev_space = False
    for ch in text.lower():
        if ch.isalpha():
            out.append(ch)
            prev_space = False
        elif not prev_space:
            out.append(" ")
            prev_space = True
    s = " " + "".join(out).strip() + " "
    n = _LID.n
    return [s[i : i + n] for i in range(len(s) - n + 1)] if len(s) >= n else []


def _lid_score(grams: list[str], lang: str) -> float:
    profile = _LID.profiles[lang]
    denom = _LID.log_denom[lang]
    # sum of log((count+1)/(total+V)); order-independent -> hash-seed-independent.
    return sum(math.log(profile.get(g, 0) + 1) - denom for g in grams)


def detect_language(text: str) -> str:
    """Return ``en``/``uk``/``ru``.

    Majority script decides Latin (``en``) vs Cyrillic; Ukrainian-unique letters
    (і, ї, є, ґ) vs Russian-unique ones (ы, э, ъ, ё) settle the definitive cases; the
    remaining short Cyrillic text is classified by a char-3-gram naive-Bayes model.
    Deterministic and reproducible. Empty / Latin-majority input is English.
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
    grams = _lid_grams(text)
    if not grams:
        return "uk"  # nothing to score -> Ukrainian-facing default
    return "uk" if _lid_score(grams, "uk") >= _lid_score(grams, "ru") else "ru"


def pack_for_code(code: str) -> LanguagePack:
    return _PACKS.get(code, _EN)


def pack_for_text(text: str) -> LanguagePack:
    return pack_for_code(detect_language(text))
