"""Corroboration-status tracking — the /case overlay and verification progress."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app
from bive.cogveritas.service import analyze_verifiability

API = "2026-06-11"
CASE = "/api/v1/cogveritas/case"
_TXT = "Я передав Петру 5000 гривень. Я підписав договір оренди."


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_default_progress_is_all_pending() -> None:
    out = analyze_verifiability(_TXT)
    p = out.verification_progress
    assert p.total == len(out.corroboration_worklist)
    assert p.pending == p.total and p.confirmed == 0 and p.refuted == 0


def test_status_overlay_updates_item_and_progress() -> None:
    base = analyze_verifiability(_TXT)
    cid = base.corroboration_worklist[0].claim_id
    out = analyze_verifiability(_TXT, {cid: {"status": "confirmed", "note": "звірено з випискою"}})
    item = next(w for w in out.corroboration_worklist if w.claim_id == cid)
    assert item.status == "confirmed"
    assert item.note == "звірено з випискою"
    assert out.verification_progress.confirmed == 1
    assert out.verdict is None


def test_invalid_status_value_is_ignored_stays_pending() -> None:
    base = analyze_verifiability(_TXT)
    cid = base.corroboration_worklist[0].claim_id
    out = analyze_verifiability(_TXT, {cid: {"status": "guilty"}})  # not a valid status
    item = next(w for w in out.corroboration_worklist if w.claim_id == cid)
    assert item.status == "pending"


@pytest.mark.contract
def test_case_endpoint_applies_statuses(client: TestClient) -> None:
    base = client.post(f"/api/v1/cogveritas/verifiability?api-version={API}", content=_TXT).json()
    cid = base["corroboration_worklist"][0]["claim_id"]
    r = client.post(
        f"{CASE}?api-version={API}",
        json={"text": _TXT, "statuses": {cid: {"status": "refuted", "note": "немає запису"}}},
    )
    assert r.status_code == 200
    d = r.json()
    assert d["verdict"] is None
    assert d["verification_progress"]["refuted"] == 1
    assert any(w["status"] == "refuted" for w in d["corroboration_worklist"])


@pytest.mark.contract
def test_case_endpoint_markdown_includes_progress(client: TestClient) -> None:
    r = client.post(f"{CASE}?api-version={API}", json={"text": _TXT, "format": "markdown"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "Прогрес перевірки" in r.text


@pytest.mark.contract
def test_case_endpoint_fails_closed_on_empty(client: TestClient) -> None:
    assert client.post(f"{CASE}?api-version={API}", json={"text": "  "}).status_code == 422


@pytest.mark.contract
def test_case_endpoint_rejects_non_object_body(client: TestClient) -> None:
    assert client.post(f"{CASE}?api-version={API}", json=[1, 2, 3]).status_code == 422
