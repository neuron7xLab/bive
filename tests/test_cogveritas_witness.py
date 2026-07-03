"""Cross-witness analysis — speaker parsing and cross-speaker relations."""

from __future__ import annotations

from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.witness import (
    analyze_by_speaker,
    cross_witness,
    distinct_speakers,
    parse_statements,
)

_CASE = (
    "Свідок1: 3 березня о 14:30 я передав Петру 5000 гривень.\n"
    "Свідок2: Петро отримав 5000 гривень того дня.\n"
    "Свідок3: Петро не отримував жодних грошей.\n"
)


def test_parse_statements_attributes_speakers() -> None:
    st = parse_statements(_CASE)
    assert [s for s, _ in st] == ["Свідок1", "Свідок2", "Свідок3"]


def test_time_prefix_is_not_mistaken_for_speaker() -> None:
    st = parse_statements("14:30 я був удома.")
    assert st[0][0] == ""  # "14" is not a speaker label


def test_distinct_speakers_preserves_order() -> None:
    assert distinct_speakers(analyze_by_speaker(_CASE)) == ["Свідок1", "Свідок2", "Свідок3"]


def test_cross_contradiction_between_speakers() -> None:
    items = cross_witness(analyze_by_speaker(_CASE))
    kinds = {i["type"] for i in items}
    assert "cross_contradiction" in kinds
    # The contradiction must be between two different speakers.
    contra = next(i for i in items if i["type"] == "cross_contradiction")
    assert contra["speakers"][0] != contra["speakers"][1]


def test_service_populates_witnesses_and_verdict_stays_null() -> None:
    out = analyze_verifiability(_CASE)
    assert out.witnesses == ["Свідок1", "Свідок2", "Свідок3"]
    assert out.cross_witness
    assert out.verdict is None


def test_single_speaker_has_no_cross_witness() -> None:
    out = analyze_verifiability("Я передав гроші. Я не передавав грошей.")
    assert out.witnesses == []
    assert out.cross_witness == []
