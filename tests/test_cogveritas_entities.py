"""Case entity index — clustering inflected mentions, filtering noise."""

from __future__ import annotations

from bive.cogveritas.entities import extract_entities
from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.verifiability_tagger import analyze


def _entities(text: str) -> list[dict[str, object]]:
    _, claims = analyze(text)
    return extract_entities(claims)


def test_sentence_initial_adverb_is_not_an_entity() -> None:
    # Regression: "Пізніше"/"Позже" (later) etc. are capitalised at sentence start and
    # were mis-listed as named entities — a glaring credibility bug in the output.
    for text, adverb in (
        ("Пізніше він заплатив 500 гривень Петрові.", "Пізніше"),
        ("Позже он передал деньги Ивану.", "Позже"),
        ("Спочатку ми зустрілись, потім пішли.", "Спочатку"),
    ):
        canon = {str(e["canonical"]) for e in _entities(text)}
        assert adverb not in canon, f"{adverb!r} wrongly listed as an entity in {canon}"


def test_inflected_mentions_cluster_to_one_entity() -> None:
    ents = _entities(
        "Я зустрів Петра увечері. Петро прийшов до банку. Я віддав Петру гроші."
    )
    petro = next(e for e in ents if "Петр" in str(e["canonical"]))
    assert petro["count"] == 3
    assert set(petro["forms"]) == {"Петро", "Петра", "Петру"}


def test_distinct_names_stay_separate() -> None:
    ents = _entities("Іван зустрів Оксану біля Хрещатика.")
    canon = {str(e["canonical"]) for e in ents}
    assert any("Іван" in c for c in canon)
    assert any("Оксан" in c for c in canon)


def test_sentence_initial_pronouns_are_not_entities() -> None:
    # "Він"/"Потім"/"Це" are capitalised function words, not entities.
    ents = _entities("Він прийшов. Потім пішов. Це сталося швидко.")
    assert ents == []


def test_entities_ranked_by_mention_count() -> None:
    ents = _entities(
        "Петро прийшов додому. Петра знову бачили тут. Петру дали гроші. Іван прийшов пізніше."
    )
    assert str(ents[0]["canonical"]).startswith("Петр")
    assert int(ents[0]["count"]) >= int(ents[-1]["count"])


def test_service_exposes_entities_verdict_null() -> None:
    out = analyze_verifiability("3 березня Петро Коваленко передав Петру 5000 гривень.")
    assert out.entities
    assert out.verdict is None
