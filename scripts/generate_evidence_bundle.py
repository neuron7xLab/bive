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
# Volatile runtime signal (wall-clock durations, generation time, HEAD sha) is kept
# OUT of the committed evidence so gates.json/EVIDENCE_BUNDLE.json are byte-reproducible
# at a given commit — the tree does not go dirty on regeneration. Provenance of the
# commit is git's job (the file lives in a commit); timing is observability, not evidence.
# This sink is .gitignore'd.
TELEMETRY_OUT = ROOT / "artifacts" / "verification" / "EVIDENCE_TELEMETRY.json"
# sha256-pinned evidence: reproducible committed artifacts whose bytes are a pure
# function of the commit. A drift in any of these is real tampering, so pin them.
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
]
# Witnessed-not-pinned: inherently volatile artifacts the release battery regenerates
# with time/environment-dependent content (pip-audit.json embeds a generated_at stamp
# and the live CVE-database result, so its sha256 changes every run). Pinning them
# would make the bundle irreproducible — the same reason the manifest refuses to pin
# them. We still record their existence (the audit must have produced output) but do
# not claim a reproducible hash for a non-reproducible file.
WITNESSED = [
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


def _run_gate(command: list[str]) -> tuple[dict[str, Any], float]:
    """Run a gate; return its deterministic record and the (volatile) wall-clock duration.

    The record carries only content that is a pure function of the commit — command,
    result, exit code, failure excerpt. Duration is returned separately so it can be
    written to telemetry and never leaks into the committed evidence.
    """
    started = perf_counter()
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    duration = round(perf_counter() - started, 3)
    output = (result.stdout + result.stderr).strip()
    record = {
        "command": command,
        "result": "pass" if result.returncode == 0 else "fail",
        "exit_code": result.returncode,
        "failure_excerpt": output[-2000:] if result.returncode != 0 else "",
    }
    return record, duration


def main() -> int:
    results = [_run_gate(command) for command in GATE_COMMANDS]
    gates = [record for record, _ in results]
    GATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    gates_payload = {
        "schema_version": 1,
        "status": "pass" if all(gate["result"] == "pass" for gate in gates) else "fail",
        "gates": gates,
    }
    GATES_OUT.write_text(json.dumps(gates_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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
    # Witnessed entries: record existence only — a reproducible hash is impossible for
    # these (see WITNESSED). `volatile: True` marks that the absent sha256 is by design,
    # not a generation failure.
    for relative in WITNESSED:
        path = ROOT / relative
        entries.append({"path": relative, "exists": path.exists(), "volatile": True})
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
                "gates_path": "artifacts/verification/gates.json",
                "entries": entries,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    # Volatile observability sink — NOT committed. Keeps the timing/provenance signal
    # without polluting the byte-reproducible evidence above.
    TELEMETRY_OUT.write_text(
        json.dumps(
            {
                "generated_at": _utc(),
                "commit": _commit(),
                "gate_durations_seconds": {
                    " ".join(record["command"]): duration for record, duration in results
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    if status != "pass":
        raise SystemExit("EVIDENCE_BUNDLE_FAIL gates failed")
    print("EVIDENCE_BUNDLE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
