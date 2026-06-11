from __future__ import annotations

from fastapi.testclient import TestClient

from bive.api import app


def test_science_registry_endpoint_exposes_boundaries() -> None:
    response = TestClient(app).get("/api/v1/system/science-registry?api-version=2026-06-11")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "bounded_reference_registry"
    assert data["reference_count"] >= 8
    assert any("must not emit person-level" in item for item in data["hard_boundaries"])


def test_system_status_contains_science_and_dynamic_gates() -> None:
    response = TestClient(app).get("/api/v1/system/status?api-version=2026-06-11")

    assert response.status_code == 200
    gate_names = {gate["name"] for gate in response.json()["gates"]}
    assert "science-registry" in gate_names
    assert "dynamic-probe" in gate_names
