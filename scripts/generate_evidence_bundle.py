from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "verification" / "EVIDENCE_BUNDLE.json"
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    entries = []
    for relative in INCLUDE:
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"status": "pass", "entries": entries}, indent=2), encoding="utf-8")
    print("EVIDENCE_BUNDLE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
