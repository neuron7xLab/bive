from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

os.environ.setdefault("BIVE_STORAGE", str(Path(tempfile.gettempdir()) / "bive-api-smoke.sqlite3"))

VALID_STATUSES = {"inconclusive", "review_required", "low_risk", "elevated_risk", "invalid_input"}
API_VERSION = "2026-06-11"


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _payload() -> dict[str, Any]:
    return {
        "subject_scope": "smoke",
        "segments": [{"speaker": "s", "text": "Я ніколи цього не робив, можливо бачив раніше."}],
    }


def _request(base_url: str, method: str, path: str, *, token: str | None = None, body: dict[str, Any] | None = None) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"content-type": "application/json"}
    if token:
        headers["x-bive-api-key"] = token
    target = base_url.rstrip("/") + path
    if not target.startswith(("http://", "https://")):
        raise ValueError(f"smoke target must be http(s); got {target!r}")
    req = urllib.request.Request(target, data=data, headers=headers, method=method)
    try:
        # Scheme asserted http(s) above; target is an operator-supplied API base URL.
        with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310  # nosec B310
            return int(response.status), response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8")


def run_remote(base_url: str, token: str | None) -> None:
    code, body = _request(base_url, "GET", "/readyz", token=token)
    ensure(code == 200, body)
    code, body = _request(base_url, "GET", f"/api/v1/system/aos-kernel?api-version={API_VERSION}", token=token)
    ensure(code == 200, body)
    code, body = _request(
        base_url,
        "POST",
        f"/api/v1/reports/from-transcript?api-version={API_VERSION}",
        token=token,
        body=_payload(),
    )
    ensure(code == 200, body)
    parsed = json.loads(body)
    ensure(parsed["report"]["final_status"] in VALID_STATUSES, body)


def run_in_process(token: str | None = None) -> None:
    try:
        from fastapi.testclient import TestClient
    except ImportError as exc:
        raise RuntimeError("MISSING_DEPENDENCY: fastapi. Install with pip install -e '.[api]'.") from exc
    from bive.api import app

    client = TestClient(app)
    environment = os.getenv("BIVE_ENV", "local").lower()
    if environment in {"staging", "production", "prod"} and not token:
        denied = client.get("/readyz")
        ensure(denied.status_code == 503, denied.text)
        return
    headers = {"x-bive-api-key": token} if token else {}
    health = client.get("/health")
    ensure(health.status_code == 200, health.text)
    ready = client.get("/readyz")
    ensure(ready.status_code == 200, ready.text)
    aos = client.get(f"/api/v1/system/aos-kernel?api-version={API_VERSION}", headers=headers)
    ensure(aos.status_code == 200, aos.text)
    ensure(aos.json()["eval_tasks"] >= 20, aos.text)
    res = client.post(f"/api/v1/reports/from-transcript?api-version={API_VERSION}", json=_payload(), headers=headers)
    ensure(res.status_code == 200, res.text)
    body = res.json()
    ensure(body["report"]["final_status"] in VALID_STATUSES, str(body))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", help="Run smoke against an already running API base URL.")
    parser.add_argument("--token", default=os.getenv("BIVE_API_TOKEN"), help="API token for staging/production smoke.")
    args = parser.parse_args()
    if args.base_url:
        run_remote(args.base_url, args.token)
    else:
        run_in_process(args.token)
    print("API_SMOKE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
