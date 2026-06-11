from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "security" / "stride_threat_model.json"
ARTIFACT = ROOT / "artifacts" / "verification" / "THREAT_MODEL_VALIDATION.json"
REQUIRED_STRIDE = {"Spoofing", "Tampering", "Repudiation", "Information Disclosure", "Denial of Service", "Elevation of Privilege"}


def _load() -> dict[str, Any]:
    if not MODEL.exists():
        raise SystemExit(f"THREAT_MODEL_FAIL missing {MODEL.relative_to(ROOT)}")
    data = json.loads(MODEL.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("THREAT_MODEL_FAIL model must be a JSON object")
    return data


def _require_list(data: dict[str, Any], name: str, minimum: int) -> list[dict[str, Any]]:
    value = data.get(name)
    if not isinstance(value, list) or len(value) < minimum:
        raise SystemExit(f"THREAT_MODEL_FAIL {name} must contain at least {minimum} entries")
    if not all(isinstance(item, dict) for item in value):
        raise SystemExit(f"THREAT_MODEL_FAIL {name} entries must be objects")
    return value


def main() -> int:
    data = _load()
    errors: list[str] = []
    _require_list(data, "assets", 5)
    _require_list(data, "trust_boundaries", 4)
    flows = _require_list(data, "data_flows", 5)
    threats = _require_list(data, "threats", 6)
    covered = {str(item.get("stride")) for item in threats}
    missing = sorted(REQUIRED_STRIDE - covered)
    if missing:
        errors.append(f"missing STRIDE categories: {missing}")
    for flow in flows:
        for key in ("id", "from", "to", "boundary", "controls"):
            if key not in flow:
                errors.append(f"data flow {flow.get('id', '<unknown>')} missing {key}")
    for threat in threats:
        for key in ("id", "stride", "boundary", "scenario", "mitigations", "verification"):
            if not threat.get(key):
                errors.append(f"threat {threat.get('id', '<unknown>')} missing {key}")
        if not isinstance(threat.get("mitigations"), list) or len(threat["mitigations"]) < 1:
            errors.append(f"threat {threat.get('id', '<unknown>')} needs at least one mitigation")
    if errors:
        raise SystemExit("THREAT_MODEL_FAIL\n" + "\n".join(f"- {e}" for e in errors))
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {
                "status": "pass",
                "model": str(MODEL.relative_to(ROOT)),
                "assets": len(data["assets"]),
                "trust_boundaries": len(data["trust_boundaries"]),
                "data_flows": len(data["data_flows"]),
                "threats": len(data["threats"]),
                "stride_coverage": sorted(covered),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("THREAT_MODEL_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
