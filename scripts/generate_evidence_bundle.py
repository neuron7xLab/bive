from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "verification" / "EVIDENCE_BUNDLE.json"
GATES_OUT = ROOT / "artifacts" / "verification" / "gates.json"
INCLUDE = [
    "ARTIFACT_MANIFEST.json",
    "PRODUCT_SYSTEM_INDEX.json",
    "SOURCE_REGISTRY.yaml",
    "docs/openapi.json",
    "artifacts/verification/DEPENDENCY_CONTRACT_VALIDATION.json",
    "artifacts/verification/TEST_ARCHITECTURE.json",
    "artifacts/verification/AUTOMATION_CONTRACT.json",
    "artifacts/verification/BIBLIOGRAPHY_VALIDATION.json",
    "artifacts/verification/DYNAMIC_ENVIRONMENT_PROBE.json",
    "artifacts/security/pip-audit.json",
]
GATE_COMMANDS = [
    ["python", "scripts/validate_dependency_contracts.py"],
    ["python", "scripts/validate_test_architecture.py"],
    ["python", "scripts/validate_automation_contract.py"],
    ["python", "scripts/validate_bibliography.py"],
]


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _run_gate(command: list[str]) -> dict[str, Any]:
    started = perf_counter()
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    output = (result.stdout + result.stderr).strip()
    return {
        "command": command,
        "result": "pass" if result.returncode == 0 else "fail",
        "exit_code": result.returncode,
        "duration_seconds": round(perf_counter() - started, 3),
        "failure_excerpt": output[-2000:] if result.returncode != 0 else "",
    }


def main() -> int:
    gates = [_run_gate(command) for command in GATE_COMMANDS]
    GATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    gates_payload = {
        "schema_version": 1,
        "generated_at": _utc(),
        "commit": _commit(),
        "status": "pass" if all(gate["result"] == "pass" for gate in gates) else "fail",
        "gates": gates,
    }
    GATES_OUT.write_text(json.dumps(gates_payload, indent=2, sort_keys=True), encoding="utf-8")

    entries = []
    for relative in INCLUDE + ["artifacts/verification/gates.json"]:
        path = ROOT / relative
        entries.append(
            {
                "path": relative,
                "exists": path.exists(),
                "sha256": _sha256(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    missing = [entry["path"] for entry in entries if not entry["exists"]]
    if missing:
        raise SystemExit(f"EVIDENCE_BUNDLE_FAIL missing={missing}")
    status = "pass" if gates_payload["status"] == "pass" else "fail"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": status,
                "generated_at": _utc(),
                "commit": gates_payload["commit"],
                "gates_path": "artifacts/verification/gates.json",
                "entries": entries,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    if status != "pass":
        raise SystemExit("EVIDENCE_BUNDLE_FAIL gates failed")
    print("EVIDENCE_BUNDLE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
