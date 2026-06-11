from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from bive.api import app
from bive.pipeline import analyze_transcript_payload
from bive.science import science_registry_summary


def test_report_never_emits_person_level_lie_label() -> None:
    report = analyze_transcript_payload(
        {
            "segments": [
                {"speaker": "a", "text": "I was at home at 9."},
                {"speaker": "a", "text": "I was not at home at 9."},
            ]
        }
    ).to_dict()
    volatile_free = dict(report)
    volatile_free.pop("policy_boundaries", None)
    volatile_free.pop("policy_invariants", None)
    blob = json.dumps(volatile_free, ensure_ascii=False).lower()
    assert "liar" not in blob
    assert "guilty" not in blob
    assert "diagnosis" not in blob


def test_science_summary_exposes_hard_boundaries() -> None:
    summary = science_registry_summary()
    joined = "\n".join(summary["hard_boundaries"]).lower()
    assert "automatic lie detection" in joined
    assert "diagnosis" in joined
    assert summary["reference_count"] >= 14


def test_api_capabilities_expose_review_not_accusation_boundary() -> None:
    data = TestClient(app).get("/api/v1/capabilities?api-version=2026-06-11").json()
    joined = "\n".join(data["invariants"]).lower()
    assert "no automatic person-level liar label" in joined
    assert "human review" in joined


def test_api_validation_error_uses_standard_error_envelope() -> None:
    response = TestClient(app).post("/api/v1/reports/from-transcript?api-version=2026-06-11", json={"segments": []})
    assert response.status_code == 422
    payload = response.json()
    assert set(payload) == {"error"}
    assert payload["error"]["code"] == "ValidationError"
    assert payload["error"]["innererror"]["requestId"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_api_runtime_limit_rejects_too_many_segments() -> None:
    response = TestClient(app).post(
        "/api/v1/reports/from-transcript?api-version=2026-06-11",
        json={"segments": [{"text": "x"} for _ in range(2001)]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"ValidationError", "too_many_segments"}


def test_frontend_source_keeps_safe_dom_rendering_boundary() -> None:
    js = Path("src/bive/web/static/app.js").read_text()
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    assert "textContent" in js
