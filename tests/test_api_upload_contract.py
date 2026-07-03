from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app

API = "2026-06-11"

SRT = (
    "1\n"
    "00:00:00,000 --> 00:00:04,200\n"
    "Alice: I never received that money.\n"
    "\n"
    "2\n"
    "00:00:08,000 --> 00:00:12,500\n"
    "Alice: I received that money later.\n"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.contract
def test_upload_srt_builds_report(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/reports/from-upload?api-version={API}",
        content=SRT,
        headers={"x-bive-filename": "case.srt", "content-type": "text/plain"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_format"] == "srt"
    assert data["segment_count"] == 2
    assert data["report_id"].startswith("bive-report-")
    assert data["report"]["policy_invariants"]


@pytest.mark.contract
def test_upload_format_query_forces_parser(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/reports/from-upload?api-version={API}&format=txt",
        content="Alice: hello\nBob: goodbye\n",
    )
    assert response.status_code == 200
    assert response.json()["detected_format"] == "txt"


@pytest.mark.contract
def test_upload_requires_api_version(client: TestClient) -> None:
    response = client.post("/api/v1/reports/from-upload", content=SRT)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MissingApiVersionParameter"


@pytest.mark.contract
def test_upload_rejects_empty_body(client: TestClient) -> None:
    response = client.post(f"/api/v1/reports/from-upload?api-version={API}", content="")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_upload"


@pytest.mark.contract
def test_upload_rejects_invalid_utf8(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/reports/from-upload?api-version={API}",
        content=b"\xff\xfe\x00\x01",
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_utf8"


@pytest.mark.contract
def test_upload_rejects_unsupported_format(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/reports/from-upload?api-version={API}&format=pdf",
        content="whatever",
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_format"


@pytest.mark.contract
def test_upload_unparseable_content_returns_422(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/reports/from-upload?api-version={API}&format=json",
        content="{not json",
    )
    assert response.status_code == 422
    assert "transcript_parse_error" in response.json()["error"]["code"]


@pytest.mark.contract
def test_capabilities_advertise_input_formats(client: TestClient) -> None:
    response = client.get(f"/api/v1/capabilities?api-version={API}")
    assert response.status_code == 200
    formats = response.json()["input_formats"]
    assert "srt" in formats
    assert "vtt" in formats


@pytest.mark.security
def test_upload_enforces_segment_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import dataclasses

    from bive import api_runtime

    tightened = dataclasses.replace(api_runtime.settings, max_segments=1)
    monkeypatch.setattr(api_runtime, "settings", tightened)
    body = "a: one\nb: two\nc: three\n"
    response = client.post(
        f"/api/v1/reports/from-upload?api-version={API}&format=txt",
        content=body,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "too_many_segments"
