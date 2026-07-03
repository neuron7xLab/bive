"""Transcript ingestion — structured formats flattened to speaker statements."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app
from bive.cogveritas.ingest import to_statement_text
from bive.cogveritas.service import analyze_verifiability

API = "2026-06-11"
EP = "/api/v1/cogveritas/verifiability"

_SRT = (
    "1\n00:00:01,000 --> 00:00:04,000\nПетро: Я передав 5000 гривень 3 березня.\n\n"
    "2\n00:00:05,000 --> 00:00:08,000\nІван: Я був удома весь вечір.\n"
)
_JSON = '[{"speaker":"Свідок А","text":"Я заплатив 3000 гривень."},{"speaker":"Свідок Б","text":"Я нічого не платив."}]'


def test_srt_flattens_to_speaker_lines() -> None:
    flat = to_statement_text(_SRT, "case.srt")
    assert "Петро: Я передав" in flat
    assert "Іван: Я був удома" in flat
    assert "-->" not in flat  # timing stripped


def test_plain_prose_without_filename_is_untouched() -> None:
    prose = "Я був у Києві, потім поїхав додому, все нормально того дня."
    assert to_statement_text(prose, None) == prose


def test_unparseable_structured_falls_back_to_raw() -> None:
    junk = "not really srt content at all"
    assert to_statement_text(junk, "x.srt") == junk


def test_json_transcript_yields_speaker_profiles() -> None:
    flat = to_statement_text(_JSON, "case.json")
    out = analyze_verifiability(flat)
    assert {p.speaker for p in out.speaker_profiles} == {"Свідок А", "Свідок Б"}
    assert all(p.total >= 1 for p in out.speaker_profiles)
    assert out.verdict is None


@pytest.mark.contract
def test_endpoint_ingests_srt_via_filename_header() -> None:
    client = TestClient(app)
    r = client.post(
        f"{EP}?api-version={API}",
        content=_SRT,
        headers={"x-bive-filename": "interrogation.srt"},
    )
    assert r.status_code == 200
    d = r.json()
    assert set(d["witnesses"]) == {"Петро", "Іван"}
    assert d["verdict"] is None
