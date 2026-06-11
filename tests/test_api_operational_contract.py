from fastapi.testclient import TestClient

from bive.api import app


def test_system_status_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/system/status?api-version=2026-06-11", headers={"x-request-id": "ops-1"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "ops-1"
    data = response.json()
    assert data["service"] == "BIVE"
    assert data["readiness"] in {"ready", "not_ready"}
    assert data["limits"]["max_segments"] > 0
    assert data["storage"]["report_count"] >= 0
    assert any(gate["name"] == "wheel-smoke" for gate in data["gates"])


def test_design_contract_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/system/design-contract?api-version=2026-06-11")
    assert response.status_code == 200
    data = response.json()
    assert "FastAPI" in data["product_layer"]
    assert "WCAG 2.2" in data["accessibility_target"]
    assert "no automatic" in data["evidence_policy"]


def test_error_envelope_and_security_headers() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/from-transcript?api-version=2026-06-11",
        json={"segments": [{"text": "valid", "extra": True}]},
        headers={"x-request-id": "bad-schema"},
    )
    assert response.status_code == 422
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    data = response.json()
    assert data["error"]["code"] == "ValidationError"
    assert data["error"]["innererror"]["requestId"] == "bad-schema"
    assert data["error"]["details"]


def test_interface_contract_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/system/interface-contract?api-version=2026-06-11")
    assert response.status_code == 200
    data = response.json()
    assert "safe DOM rendering for dynamic report fields" in data["frontend_controls"]
    assert "security headers" in data["backend_controls"]
