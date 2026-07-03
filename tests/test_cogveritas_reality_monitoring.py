"""Reality Monitoring — per-claim detail profile, framed as a review aid."""

from __future__ import annotations

from bive.cogveritas.reality_monitoring import rm_profiles
from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.verifiability_tagger import analyze


def _rm(text: str) -> list[dict[str, object]]:
    _, claims = analyze(text)
    return rm_profiles(claims)


def test_rich_claim_scores_multiple_detail_criteria() -> None:
    rm = _rm("Я бачив червоне авто о 14:30 біля станції на вулиці Банкова.")
    assert rm
    top = rm[0]
    assert top["temporal"] is True
    assert top["spatial"] is True
    assert top["perceptual"] is True  # "бачив"
    assert int(top["detail_count"]) >= 3


def test_opinion_claim_marks_cognitive_operations() -> None:
    rm = _rm("Я думаю, що все було погано насправді.")
    assert rm
    assert rm[0]["cognitive_operations"] is True
    assert int(rm[0]["detail_count"]) == 0


def test_detail_free_claim_is_omitted() -> None:
    # No temporal/spatial/perceptual/quantitative signal and no cognitive marker.
    assert _rm("Він пішов кудись туди.") == []


def test_service_exposes_rm_profiles_verdict_null() -> None:
    out = analyze_verifiability("Я чув гучний звук о 3:00 біля дому.")
    assert out.rm_profiles
    assert all(p.claim_id for p in out.rm_profiles)
    assert out.verdict is None
