"""Language layer: detection + Ukrainian/Russian verifiability tagging."""

from __future__ import annotations

import pytest

from bive.cogveritas.lang import detect_language, pack_for_text
from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.verifiability_tagger import analyze, classify_claim_verifiability


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Я був у Києві вчора о 14:30", "uk"),
        ("Свідок передав 5000 гривень на вулиці Банковій", "uk"),
        ("Я был в Москве вчера, это точно произошло", "ru"),
        ("Он передал деньги в подъезде", "ru"),
        ("I met John at the Hilton on March 3", "en"),
        ("", "en"),
        ("12345 67890 !!!", "en"),
        # Russian carrying no orthography-unique letters and no listed function words —
        # disambiguated by the -л masculine-past ending, not defaulted to Ukrainian.
        ("Иван купил машину.", "ru"),
        ("Иван купил машину вчера.", "ru"),
        ("Николай сказал правду.", "ru"),
        # Ukrainian -в past stays Ukrainian.
        ("Микола зробив помилку.", "uk"),
    ],
)
def test_language_detection(text: str, expected: str) -> None:
    assert detect_language(text) == expected


def test_russian_without_unique_letters_routes_to_russian_pack() -> None:
    # Regression: the whole anchor set (temporal etc.) must follow the right language.
    out = analyze_verifiability("Иван купил машину вчера.")
    assert out.detected_language == "ru"
    assert out.verdict is None


def test_ukrainian_end_to_end_separates_checkable_from_opinion() -> None:
    text = (
        "3 березня о 14:30 я зустрів Петра Коваленка біля станції Хрещатик. "
        "Він передав мені 5000 гривень. "
        "Я думаю, що він нервував, здавалося, був стурбований."
    )
    out = analyze_verifiability(text)
    assert out.verdict is None  # invariant holds in every language
    labels = [n.verifiability for n in out.audit_trail]
    assert "externally_checkable" in labels
    assert "not_externally_checkable" in labels  # the opinion sentence
    # Ukrainian phrasing, not English.
    assert any("незалежний запис" in q for q in out.corroboration_questions)
    assert any("голослівне" in n for n in out.rm_criteria_flagged)


def test_russian_produces_russian_phrasing() -> None:
    text = "5 мая в 18:00 он передал 3000 долларов возле дома на улице Ленина."
    out = analyze_verifiability(text)
    assert out.verdict is None
    assert any("независимая запись" in q for q in out.corroboration_questions)


def test_opinion_markers_are_language_specific() -> None:
    _, claims = analyze("Я думаю, здається, мабуть, це було десь там.")
    assert claims and all(c.lang == "uk" for c in claims)
    # An all-opinion Ukrainian sentence must not be externally checkable.
    assert classify_claim_verifiability(claims[0]) == "not_externally_checkable"


def test_english_regression_still_english() -> None:
    out = analyze_verifiability("I met John Smith at the Hilton on March 3 and paid 500 dollars.")
    assert out.verdict is None
    assert any("independent record" in q for q in out.corroboration_questions)
    assert pack_for_text("plain english text here").code == "en"


@pytest.mark.parametrize(
    "opinion",
    [
        "This is beautiful.",
        "There was nothing here.",
        "Maybe it was wrong here.",
    ],
)
def test_capitalised_function_words_are_not_entity_anchors(opinion: str) -> None:
    # Regression: sentence-initial "This"/"There"/"Maybe" were counted as proper-noun
    # anchors, tagging pure opinion as externally checkable and understating the gap.
    _, claims = analyze(opinion)
    assert claims
    assert classify_claim_verifiability(claims[0]) == "not_externally_checkable"


def test_real_named_entities_stay_checkable() -> None:
    # The stop-name filter must not suppress genuine proper-noun anchors.
    _, claims = analyze("Ivan signed the contract on 5 May.")
    assert claims
    assert classify_claim_verifiability(claims[0]) == "externally_checkable"


def test_ukrainian_apostrophe_word_is_one_token() -> None:
    # Regression: "під'їзд" was split into ['під', 'їзд'], making the apostrophe-bearing
    # spatial anchor unreachable by token membership.
    from bive.cogveritas.lang import pack_for_code

    assert pack_for_code("uk").word.findall("під'їзд") == ["під'їзд"]
    _, claims = analyze("Це був під'їзд будинку.")
    assert claims
    assert "під'їзд" in [t.lower() for t in claims[0].tokens]
