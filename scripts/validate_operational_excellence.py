from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "operations" / "service_slo.json"
ARTIFACT = ROOT / "artifacts" / "verification" / "OPERATIONAL_EXCELLENCE_VALIDATION.json"
REQUIRED_PILLARS = {"reliability", "security", "operational_excellence", "performance_efficiency", "cost_optimization"}
REQUIRED_OBSERVABILITY = {"x-ms-request-id", "x-ms-client-request-id", "/readyz", "/metrics"}


def main() -> int:
    data: dict[str, Any] = json.loads(MODEL.read_text(encoding="utf-8"))
    errors: list[str] = []
    pillars = set(data.get("well_architected_pillars", []))
    missing_pillars = sorted(REQUIRED_PILLARS - pillars)
    if missing_pillars:
        errors.append(f"missing pillars: {missing_pillars}")
    if len(data.get("service_level_objectives", [])) < 4:
        errors.append("at least four service level objectives required")
    if len(data.get("release_rings", [])) < 3:
        errors.append("at least three release rings required")
    rollback = data.get("rollback_policy", {})
    if not rollback.get("trigger") or not rollback.get("action"):
        errors.append("rollback policy requires triggers and actions")
    observability = "\n".join(data.get("observability_contract", []))
    for token in REQUIRED_OBSERVABILITY:
        if token not in observability:
            errors.append(f"observability contract missing {token}")
    if errors:
        raise SystemExit("OPERATIONAL_EXCELLENCE_FAIL\n" + "\n".join(f"- {e}" for e in errors))
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {
                "status": "pass",
                "model": str(MODEL.relative_to(ROOT)),
                "pillars": sorted(pillars),
                "slos": len(data["service_level_objectives"]),
                "release_rings": [ring["ring"] for ring in data["release_rings"]],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("OPERATIONAL_EXCELLENCE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
