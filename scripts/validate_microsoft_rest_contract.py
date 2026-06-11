from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("BIVE_STORAGE", str(Path(tempfile.gettempdir()) / "bive-ms-rest.sqlite3"))

from fastapi.testclient import TestClient

from bive.api import app
from bive.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "verification" / "MICROSOFT_REST_CONTRACT.json"


def _assert_error_shape(payload: dict[str, Any]) -> None:
    if set(payload) != {"error"}:
        raise AssertionError(f"error payload must contain only error object: {payload}")
    error = payload["error"]
    if not isinstance(error, dict):
        raise AssertionError("error must be object")
    for key in ("code", "message", "details", "innererror"):
        if key not in error:
            raise AssertionError(f"error missing {key}")
    inner = error["innererror"]
    if not isinstance(inner, dict) or not inner.get("requestId"):
        raise AssertionError("innererror.requestId missing")


def main() -> int:
    version = get_settings().api_version
    with TestClient(app) as client:
        missing = client.get("/api/v1/system/status", headers={"x-ms-client-request-id": "client-a"})
        if missing.status_code != 400:
            raise SystemExit(f"MS_REST_CONTRACT_FAIL missing api-version returned {missing.status_code}")
        _assert_error_shape(missing.json())
        if missing.json()["error"]["code"] != "MissingApiVersionParameter":
            raise SystemExit("MS_REST_CONTRACT_FAIL wrong missing api-version error code")
        bad_version = client.get("/api/v1/system/status?api-version=1900-01-01")
        if bad_version.status_code != 400:
            raise SystemExit("MS_REST_CONTRACT_FAIL bad api-version did not fail")
        _assert_error_shape(bad_version.json())
        ok = client.get(
            f"/api/v1/system/status?api-version={version}",
            headers={"x-ms-request-id": "server-correlation", "x-ms-client-request-id": "client-correlation"},
        )
        if ok.status_code != 200:
            raise SystemExit(f"MS_REST_CONTRACT_FAIL status endpoint failed: {ok.text}")
        if ok.headers.get("x-ms-request-id") != "server-correlation":
            raise SystemExit("MS_REST_CONTRACT_FAIL x-ms-request-id was not preserved")
        if ok.headers.get("x-ms-client-request-id") != "client-correlation":
            raise SystemExit("MS_REST_CONTRACT_FAIL x-ms-client-request-id was not echoed")
        invalid = client.post(
            f"/api/v1/reports/from-transcript?api-version={version}",
            json={"segments": []},
            headers={"x-ms-request-id": "invalid-report"},
        )
        if invalid.status_code != 422:
            raise SystemExit("MS_REST_CONTRACT_FAIL invalid payload did not return 422")
        _assert_error_shape(invalid.json())
        if invalid.json()["error"]["code"] != "ValidationError":
            raise SystemExit("MS_REST_CONTRACT_FAIL validation error code mismatch")
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {
                "status": "pass",
                "api_version": version,
                "checks": [
                    "api-version required",
                    "unsupported api-version rejected",
                    "x-ms-request-id propagated",
                    "x-ms-client-request-id echoed",
                    "Microsoft-style error envelope",
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print("MICROSOFT_REST_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
