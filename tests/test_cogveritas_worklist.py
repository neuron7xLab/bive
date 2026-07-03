"""Corroboration worklist — record-type routing for checkable claims."""

from __future__ import annotations

from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.verifiability_tagger import analyze
from bive.cogveritas.worklist import corroboration_worklist


def _routes(text: str) -> list[list[str]]:
    _, claims = analyze(text)
    return [item["record_types"] for item in corroboration_worklist(claims)]  # type: ignore[misc]


def test_money_claim_routes_to_financial_records() -> None:
    out = analyze_verifiability("Він передав мені 5000 гривень готівкою 3 березня.")
    joined = " ".join(r for it in out.corroboration_worklist for r in it.record_types)
    assert "банківська виписка" in joined


def test_phone_claim_routes_to_telecom() -> None:
    out = analyze_verifiability("Я подзвонив йому з мобільного о 14:30.")
    joined = " ".join(r for it in out.corroboration_worklist for r in it.record_types)
    assert "білінг" in joined


def test_place_and_time_routes_to_cctv() -> None:
    out = analyze_verifiability("О 18:00 я був біля станції Хрещатик на вулиці Хрещатик.")
    joined = " ".join(r for it in out.corroboration_worklist for r in it.record_types)
    assert "камери" in joined or "геолокація" in joined


def test_signed_document_is_checkable_and_routed() -> None:
    # A signed contract has no named-entity anchor but is highly checkable.
    out = analyze_verifiability("Я підписав договір оренди квартири.")
    assert out.corroboration_worklist, "a signed-document claim must be checkable"
    joined = " ".join(r for it in out.corroboration_worklist for r in it.record_types)
    assert "реєстр" in joined or "документа" in joined


def test_pure_opinion_is_not_in_worklist() -> None:
    out = analyze_verifiability("Я думаю, він нервував і, здається, був стурбований.")
    assert out.corroboration_worklist == []
    assert out.verdict is None


def test_english_worklist_uses_english_labels() -> None:
    routes = _routes("I paid him 500 dollars and signed the contract on Monday.")
    flat = " ".join(r for item in routes for r in item)
    assert "bank statement" in flat or "registry" in flat
