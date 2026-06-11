from fastapi.testclient import TestClient

from bive.api import app


def test_health_contract() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["allow_person_level_verdicts"] is False


def test_create_report_from_transcript() -> None:
    client = TestClient(app)
    payload = {
        "subject_scope": "test",
        "segments": [
            {"speaker": "a", "text": "Я точно ніколи не бачив цей документ."},
            {"speaker": "a", "text": "Можливо, бачив, але не пам’ятаю."},
        ],
    }
    response = client.post("/api/v1/reports/from-transcript?api-version=2026-06-11", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"].startswith("bive-report-")
    assert "report" in data
    assert data["report"]["policy_invariants"]


def test_api_rejects_extra_fields() -> None:
    client = TestClient(app)
    payload = {
        "subject_scope": "test",
        "segments": [{"speaker": "a", "text": "valid text", "unexpected": True}],
        "unexpected": True,
    }
    response = client.post("/api/v1/reports/from-transcript?api-version=2026-06-11", json=payload)
    assert response.status_code == 422


def test_api_rejects_oversized_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/from-transcript?api-version=2026-06-11",
        content=b"{}",
        headers={"content-type": "application/json", "content-length": "25000001"},
    )
    assert response.status_code == 413


def test_readiness_contract() -> None:
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_api_sets_request_id_and_metrics() -> None:
    client = TestClient(app)
    response = client.get("/health", headers={"x-request-id": "test-request-id"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-id"
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "bive_requests_total" in metrics.text
