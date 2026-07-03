"""Canonical end-to-end acceptance — a full multi-witness case through the API.

Proves the whole COGVERITAS analyst pipeline (Phases 1-7) holds together and that
the no-verdict invariant survives end to end: ingestion → entities → profiles →
cross-witness → timeline → conflicts → worklist → case status → dossier → integrity.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app
from bive.cogveritas.output_contract import FORBIDDEN_JUDGMENT_STRINGS

API = "2026-06-11"
V = "/api/v1/cogveritas/verifiability"
CASE = "/api/v1/cogveritas/case"
VERIFY = "/api/v1/cogveritas/verify-integrity"

# A multi-speaker interrogation transcript (JSON) exercising every capability.
_TRANSCRIPT = (
    '[{"speaker":"Петренко","text":"Я передав Коваленку 5000 гривень 3 березня."},'
    '{"speaker":"Петренко","text":"Я подзвонив дружині з мобільного о 14:30."},'
    '{"speaker":"Іваненко","text":"Петренко передав Коваленку 5000 гривень."},'
    '{"speaker":"Іваненко","text":"Петренко не передавав Коваленку жодних грошей."},'
    '{"speaker":"Петренко","text":"Я думаю, що він нервував."}]'
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_full_case_pipeline_end_to_end(client: TestClient) -> None:
    r = client.post(
        f"{V}?api-version={API}", content=_TRANSCRIPT, headers={"x-bive-filename": "case.json"}
    )
    assert r.status_code == 200
    d = r.json()

    # No verdict, no probability — anywhere, ever.
    assert d["verdict"] is None
    assert d["calibrated_probability"] is None

    # Every phase produced its surface.
    assert d["detected_language"] == "uk"                       # P1 language
    assert d["corroboration_worklist"]                          # P1 worklist
    assert d["timeline"]                                        # P1 timeline
    assert d["conflicts"] or d["cross_witness"]                 # P1/P2 inconsistencies
    assert set(d["witnesses"]) == {"Петренко", "Іваненко"}  # P2/P5 speakers
    assert d["speaker_profiles"]                                # P5 profiles
    assert any(x["type"] == "cross_contradiction" for x in d["cross_witness"])  # P2
    assert any("Коваленк" in e["canonical"] for e in d["entities"])            # P3 entities
    assert d["verification_progress"]["total"] == len(d["corroboration_worklist"])  # P4
    assert d["integrity"]["case_id"]                            # P6 integrity

    # A named entity clusters its inflected forms (Коваленку/Коваленко/Коваленка).
    koval = next(e for e in d["entities"] if "Коваленк" in e["canonical"])
    assert koval["count"] >= 3

    # The opinion sentence is NOT checkable; it is flagged unverifiable.
    assert any("нерв" in n for n in d["rm_criteria_flagged"])


def test_case_status_then_reproducible_integrity(client: TestClient) -> None:
    base = client.post(
        f"{V}?api-version={API}", content=_TRANSCRIPT, headers={"x-bive-filename": "case.json"}
    ).json()
    cid = base["corroboration_worklist"][0]["claim_id"]

    # Analyst confirms one item via the case endpoint (statuses drive progress).
    cased = client.post(
        f"{CASE}?api-version={API}",
        json={
            "text": _TRANSCRIPT,
            "filename": "case.json",
            "statuses": {cid: {"status": "confirmed", "note": "звірено з випискою"}},
        },
    ).json()
    assert cased["verification_progress"]["confirmed"] == 1
    assert cased["verdict"] is None

    # The stamped fingerprint reproduces exactly from the same source (chain-of-custody).
    r = client.post(
        f"{VERIFY}?api-version={API}",
        json={"text": _TRANSCRIPT, "filename": "case.json", "expected": base["integrity"]},
    )
    assert r.json()["match"] is True


def test_markdown_dossier_is_complete_and_verdict_free(client: TestClient) -> None:
    import re

    r = client.post(
        f"{CASE}?api-version={API}",
        json={"text": _TRANSCRIPT, "filename": "case.json", "format": "markdown"},
    )
    assert r.status_code == 200
    md = r.text
    for heading in ("Сутності справи", "Хронологія", "Лист корроборації", "Провенанс", "case_id"):
        assert heading in md
    # System framing (quotes stripped) must carry no person-level judgment.
    framing = re.sub(r"«[^»]*»", "«…»", md).lower()
    assert all(s not in framing for s in FORBIDDEN_JUDGMENT_STRINGS)


@pytest.mark.contract
def test_capabilities_envelope_declares_limits(client: TestClient) -> None:
    r = client.get(f"/api/v1/cogveritas/capabilities?api-version={API}")
    assert r.status_code == 200
    d = r.json()
    assert d["human_in_the_loop"] is True
    assert "uk" in d["supported_languages"]
    assert len(d["capabilities"]) >= 8
    limits = " ".join(d["hard_limits"]).lower()
    assert "verdict" in limits and "not a lie detector" in limits
