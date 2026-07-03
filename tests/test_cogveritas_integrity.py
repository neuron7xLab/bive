"""Evidence-chain integrity — deterministic, tamper-evident fingerprint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app
from bive.cogveritas.integrity import COGVERITAS_ENGINE, compute_integrity
from bive.cogveritas.service import analyze_verifiability

API = "2026-06-11"
VERIFY = "/api/v1/cogveritas/verify-integrity"
_TXT = "3 березня Петро передав 5000 гривень біля станції Хрещатик."


def test_fingerprint_is_deterministic() -> None:
    a = analyze_verifiability(_TXT).integrity
    b = analyze_verifiability(_TXT).integrity
    assert a.case_id == b.case_id
    assert a.source_sha256 == b.source_sha256
    assert a.engine == COGVERITAS_ENGINE


def test_single_char_change_alters_fingerprint() -> None:
    a = analyze_verifiability(_TXT).integrity
    b = analyze_verifiability(_TXT.replace("5000", "6000")).integrity
    assert a.case_id != b.case_id
    assert a.source_sha256 != b.source_sha256


def test_integrity_field_excluded_from_its_own_hash() -> None:
    out = analyze_verifiability(_TXT)
    # Recomputing analysis hash over the dumped payload must reproduce the stamped
    # value (i.e. the integrity block itself is not part of the hashed content).
    recomputed = compute_integrity(_TXT, out.model_dump())
    assert recomputed["analysis_sha256"] == out.integrity.analysis_sha256
    assert recomputed["case_id"] == out.integrity.case_id


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.contract
def test_verify_endpoint_confirms_matching_fingerprint(client: TestClient) -> None:
    out = client.post(f"/api/v1/cogveritas/verifiability?api-version={API}", content=_TXT).json()
    expected = out["integrity"]
    r = client.post(f"{VERIFY}?api-version={API}", json={"text": _TXT, "expected": expected})
    assert r.status_code == 200
    d = r.json()
    assert d["match"] is True
    assert d["mismatched_fields"] == []


@pytest.mark.contract
def test_verify_endpoint_detects_tamper(client: TestClient) -> None:
    out = client.post(f"/api/v1/cogveritas/verifiability?api-version={API}", content=_TXT).json()
    expected = dict(out["integrity"])
    # Same claimed fingerprint, but the source text was altered.
    r = client.post(
        f"{VERIFY}?api-version={API}",
        json={"text": _TXT.replace("Петро", "Іван"), "expected": expected},
    )
    d = r.json()
    assert d["match"] is False
    assert "case_id" in d["mismatched_fields"]


@pytest.mark.contract
def test_verify_endpoint_fails_closed_on_empty(client: TestClient) -> None:
    assert client.post(f"{VERIFY}?api-version={API}", json={"text": " "}).status_code == 422
