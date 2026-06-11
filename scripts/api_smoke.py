from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("BIVE_STORAGE", str(Path(tempfile.gettempdir()) / "bive-api-smoke.sqlite3"))

from fastapi.testclient import TestClient

from bive.api import app

VALID_STATUSES = {"inconclusive", "review_required", "low_risk", "elevated_risk", "invalid_input"}


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    client = TestClient(app)
    health = client.get("/health")
    ensure(health.status_code == 200, health.text)
    ready = client.get("/readyz")
    ensure(ready.status_code == 200, ready.text)
    payload = {
        "subject_scope": "smoke",
        "segments": [{"speaker": "s", "text": "Я ніколи цього не робив, можливо бачив раніше."}],
    }
    aos = client.get("/api/v1/system/aos-kernel?api-version=2026-06-11")
    ensure(aos.status_code == 200, aos.text)
    ensure(aos.json()["eval_tasks"] >= 20, aos.text)
    res = client.post("/api/v1/reports/from-transcript?api-version=2026-06-11", json=payload)
    ensure(res.status_code == 200, res.text)
    body = res.json()
    ensure(body["report"]["final_status"] in VALID_STATUSES, str(body))
    print("API_SMOKE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
