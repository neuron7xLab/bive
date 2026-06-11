from __future__ import annotations

import importlib
from types import ModuleType

from fastapi.testclient import TestClient


def reload_api_module(monkeypatch, tmp_path, *, env: str, token: str | None = None) -> ModuleType:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("BIVE_ENV", env)
    monkeypatch.setenv("BIVE_STORAGE", str(tmp_path / f"{env}.sqlite3"))
    if token is None:
        monkeypatch.delenv("BIVE_API_TOKEN", raising=False)
    else:
        monkeypatch.setenv("BIVE_API_TOKEN", token)
    # The FastAPI app and its settings are constructed in ``bive.api_runtime``;
    # ``bive.api`` is only a fail-closed loader. Reload the runtime first so the
    # rebuilt app observes the patched environment, then reload the loader.
    import bive.api_runtime as runtime_module

    importlib.reload(runtime_module)
    import bive.api as api_module

    return importlib.reload(api_module)


def test_staging_api_requires_token(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    api_module = reload_api_module(monkeypatch, tmp_path, env="staging", token="secret")
    client = TestClient(api_module.app)
    payload = {"segments": [{"text": "valid text"}]}

    denied = client.post("/api/v1/reports/from-transcript?api-version=2026-06-11", json=payload)
    assert denied.status_code == 401
    assert denied.json()["error"]["code"] == "authentication_required"

    allowed = client.post(
        "/api/v1/reports/from-transcript?api-version=2026-06-11",
        json=payload,
        headers={"x-bive-api-key": "secret"},
    )
    assert allowed.status_code == 200


def test_staging_readiness_fails_without_token(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    api_module = reload_api_module(monkeypatch, tmp_path, env="staging", token=None)
    client = TestClient(api_module.app)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert "BIVE_API_TOKEN is required" in response.text


def test_middleware_counts_early_rejected_payload(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    api_module = reload_api_module(monkeypatch, tmp_path, env="local")
    client = TestClient(api_module.app)
    before = client.get("/metrics").text
    response = client.post(
        "/api/v1/reports/from-transcript?api-version=2026-06-11",
        content=b"{}",
        headers={"content-type": "application/json", "content-length": "25000001"},
    )
    after = client.get("/metrics").text
    assert response.status_code == 413
    assert before != after
    assert "bive_request_errors_total" in after
