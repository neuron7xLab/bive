from __future__ import annotations

from fastapi.testclient import TestClient

from bive.api import app, settings


def test_aos_kernel_api_contract() -> None:
    client = TestClient(app)
    response = client.get(f"/api/v1/system/aos-kernel?api-version={settings.api_version}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AOS-PROMPT-KERNEL"
    assert data["eval_tasks"] >= 20
    assert data["release_gate"] == "make aos-kernel"
