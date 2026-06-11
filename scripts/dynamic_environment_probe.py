from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# Volatile fields that carry wall-clock time or per-run identifiers. They must be
# blanked at every depth, otherwise the "structural" hash drifts whenever the clock
# ticks between two report builds (nested provenance.generated_at lives inside each
# evidence event, not only in the top-level provenance list).
_VOLATILE_KEYS = frozenset({"report_id", "created_at", "generated_at", "timestamp"})


def _normalize_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<normalized>" if key in _VOLATILE_KEYS else _normalize_volatile(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_volatile(item) for item in value]
    return value


def _normalize_report(data: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_volatile(copy.deepcopy(data))
    assert isinstance(normalized, dict)
    return normalized


def _stable_hash(data: dict[str, Any]) -> str:
    payload = json.dumps(_normalize_report(data), ensure_ascii=False, sort_keys=True).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _production_auth_probe() -> dict[str, Any]:
    code = """
import os, tempfile
os.environ['BIVE_ENV']='production'
os.environ.pop('BIVE_API_TOKEN', None)
os.environ['BIVE_STORAGE']=tempfile.NamedTemporaryFile(delete=True).name
from fastapi.testclient import TestClient
from bive.api import app
payload={'subject_scope':'probe','segments':[{'speaker':'x','text':'claim one'}]}
response=TestClient(app).post('/api/v1/reports/from-transcript?api-version=2026-06-11', json=payload)
print(response.status_code)
""".strip()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    status = (
        int(result.stdout.strip().splitlines()[-1]) if result.stdout.strip().splitlines() else -1
    )
    if status not in {401, 503}:
        raise RuntimeError(f"production auth probe expected 401/503, got {status}: {result.stdout}")
    return {"status_code": status, "expected": "401_or_503"}


def main() -> int:
    temp_root = Path(tempfile.mkdtemp(prefix="bive-dynamic-"))
    os.environ.setdefault("BIVE_ENV", "test")
    os.environ["BIVE_STORAGE"] = str(temp_root / "probe.sqlite3")
    os.environ["BIVE_MAX_UPLOAD_BYTES"] = "512"

    from fastapi.testclient import TestClient

    from bive.api import app
    from bive.pipeline import analyze_transcript_payload, parse_transcript_payload
    from bive.science import load_science_registry
    from bive.storage import ReportStore

    sample = json.loads((ROOT / "samples" / "demo_transcript.json").read_text(encoding="utf-8"))
    report_a = analyze_transcript_payload(sample).to_dict()
    report_b = analyze_transcript_payload(sample).to_dict()
    hash_a = _stable_hash(report_a)
    hash_b = _stable_hash(report_b)
    if hash_a != hash_b:
        raise RuntimeError("normalized structural hash changed across repeated runs")
    if report_a["report_id"] == report_b["report_id"]:
        raise RuntimeError(
            "runtime report ids must remain unique outside deterministic artifact mode"
        )

    malformed_ok = False
    try:
        parse_transcript_payload({"segments": [{"text": ""}]})
    except ValueError:
        malformed_ok = True
    if not malformed_ok:
        raise RuntimeError("malformed transcript was not rejected")

    client = TestClient(app)
    oversized = {"segments": [{"speaker": "probe", "text": "x" * 2000}]}
    oversized_response = client.post("/api/v1/reports/from-transcript?api-version=2026-06-11", json=oversized)
    if oversized_response.status_code not in {413, 422}:
        raise RuntimeError(
            f"oversized payload expected 413/422, got {oversized_response.status_code}"
        )

    store = ReportStore(temp_root / "concurrent.sqlite3")

    def write_one(index: int) -> str:
        report = analyze_transcript_payload(
            {"segments": [{"speaker": f"s{index}", "text": f"claim number {index}"}]}
        )
        store.save(report)
        return report.report_id

    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(write_one, range(24)))
    if len(set(ids)) != 24:
        raise RuntimeError("concurrent writes produced duplicate report ids")
    if store.stats()["report_count"] != 24:
        raise RuntimeError("storage did not persist all concurrent reports")

    science = load_science_registry()
    if len(science["references"]) < 8:
        raise RuntimeError("science registry is too thin for release evidence")

    production_auth = _production_auth_probe()
    output = {
        "dynamic_probe_id": "bive-stage6-dynamic-environment-probe",
        "normalized_structural_hash": hash_a,
        "repeated_runs": "pass",
        "malformed_input": "pass",
        "oversized_payload_status": oversized_response.status_code,
        "storage_concurrent_writes": len(ids),
        "science_references": len(science["references"]),
        "production_auth_missing": production_auth,
    }
    out_path = ROOT / "artifacts" / "verification" / "DYNAMIC_ENVIRONMENT_PROBE.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DYNAMIC_ENVIRONMENT_PROBE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
