from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from bive.api import app

API_VERSION = "2026-06-11"


def _load_script(relative: str):  # type: ignore[no-untyped-def]
    path = Path(relative)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def test_microsoft_api_version_is_required() -> None:
    response = TestClient(app).get("/api/v1/system/status")
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "MissingApiVersionParameter"
    assert payload["error"]["innererror"]["requestId"]


def test_microsoft_correlation_headers_roundtrip() -> None:
    response = TestClient(app).get(
        f"/api/v1/system/status?api-version={API_VERSION}",
        headers={"x-ms-request-id": "rid-1", "x-ms-client-request-id": "cid-1"},
    )
    assert response.status_code == 200
    assert response.headers["x-ms-request-id"] == "rid-1"
    assert response.headers["x-ms-client-request-id"] == "cid-1"


def test_microsoft_error_envelope_shape() -> None:
    response = TestClient(app).post(
        f"/api/v1/reports/from-transcript?api-version={API_VERSION}",
        json={"segments": []},
        headers={"x-ms-request-id": "rid-invalid"},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert set(error) == {"code", "message", "details", "innererror"}
    assert error["code"] == "ValidationError"
    assert error["innererror"]["requestId"] == "rid-invalid"


def test_microsoft_contract_validators_pass(capsys) -> None:  # type: ignore[no-untyped-def]
    scripts = [
        ("scripts/validate_threat_model.py", "THREAT_MODEL_PASS"),
        ("scripts/validate_microsoft_rest_contract.py", "MICROSOFT_REST_CONTRACT_PASS"),
        ("scripts/validate_operational_excellence.py", "OPERATIONAL_EXCELLENCE_PASS"),
    ]
    for relative, token in scripts:
        assert _load_script(relative).main() == 0
        assert token in capsys.readouterr().out


def test_dependency_contract_requires_compiled_requirement_files() -> None:
    assert _load_script("scripts/validate_dependency_contracts.py").main() == 0
    data = json.loads(Path("artifacts/verification/DEPENDENCY_CONTRACT_VALIDATION.json").read_text())
    for filename in ("core.txt", "api.txt", "prod.txt", "dev.txt", "security.txt"):
        assert filename in data["requirement_files"]
