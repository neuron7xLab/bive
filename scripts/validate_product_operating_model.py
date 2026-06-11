from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "product" / "product_operating_model.json"
SCORECARD = ROOT / "data" / "product" / "industrial_release_scorecard.json"
OUTPUT = ROOT / "artifacts" / "verification" / "PRODUCT_READINESS.json"
FORBIDDEN_PRODUCT_CLAIMS = {
    "production deployed service",
    "lie detector",
    "diagnostic tool",
    "cve-clean without pip-audit evidence",
}
REQUIRED_DIMENSIONS = {
    "install_and_package",
    "local_tests",
    "api_contract",
    "frontend_contract",
    "science_boundary",
    "aos_kernel",
    "neurocognitive_control",
    "product_readiness",
    "dependency_cve_audit",
    "docker_runtime",
    "deployment_smoke",
    "human_impact_review",
}


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain JSON object")
    return data


def _append_missing(errors: list[str], prefix: str, data: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        if field not in data or data[field] in (None, "", [], {}):
            errors.append(f"{prefix} missing {field}")


def main() -> int:
    errors: list[str] = []
    if not MODEL.exists():
        errors.append("missing product operating model")
        model: dict[str, Any] = {}
    else:
        model = _load(MODEL)
    if not SCORECARD.exists():
        errors.append("missing industrial release scorecard")
        scorecard: dict[str, Any] = {}
    else:
        scorecard = _load(SCORECARD)

    _append_missing(errors, "model", model, ("model_id", "version", "status", "positioning", "product_principles", "jobs_to_be_done", "activation_path", "success_metrics", "release_policy", "external_standards_alignment"))
    positioning = model.get("positioning", {})
    if not isinstance(positioning, dict):
        errors.append("positioning must be object")
        positioning = {}
    _append_missing(errors, "positioning", positioning, ("category", "primary_user", "core_problem", "product_promise", "explicit_non_claims"))
    non_claims = positioning.get("explicit_non_claims", [])
    if not isinstance(non_claims, list) or len(non_claims) < 5:
        errors.append("explicit_non_claims must list hard product boundaries")
    if not any("lie detector" in str(item).lower() for item in non_claims):
        errors.append("non-claims must explicitly reject lie detector positioning")

    for collection_name, required_fields in {
        "product_principles": ("id", "name", "decision_rule", "validator"),
        "jobs_to_be_done": ("id", "job", "input", "output", "success_metric", "validator"),
        "activation_path": ("step", "name", "command", "evidence"),
        "success_metrics": ("id", "name", "target", "measurement"),
        "external_standards_alignment": ("name", "operational_use", "repo_artifact"),
    }.items():
        collection = model.get(collection_name, [])
        if not isinstance(collection, list) or not collection:
            errors.append(f"{collection_name} must be non-empty list")
            continue
        ids: list[str] = []
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                errors.append(f"{collection_name}[{index}] must be object")
                continue
            if "id" in required_fields and item.get("id"):
                ids.append(str(item["id"]))
            _append_missing(errors, f"{collection_name}[{index}]", item, tuple(required_fields))
        if ids and len(ids) != len(set(ids)):
            errors.append(f"{collection_name} ids must be unique")

    release_policy = model.get("release_policy", {})
    if not isinstance(release_policy, dict):
        errors.append("release_policy must be object")
    else:
        if release_policy.get("current_release_stage") != "public_github_candidate":
            errors.append("current release stage must be public_github_candidate")
        forbidden_claim = str(release_policy.get("forbidden_claim", "")).lower()
        if "deployed production" not in forbidden_claim:
            errors.append("release policy must forbid deployed production claim")

    _append_missing(errors, "scorecard", scorecard, ("scorecard_id", "version", "overall_status", "status_rule", "dimensions", "public_release_claims", "decision"))
    if scorecard.get("overall_status") == "GREEN":
        errors.append("overall_status cannot be GREEN while external gates remain unknown")
    dimensions = scorecard.get("dimensions", [])
    if not isinstance(dimensions, list):
        errors.append("dimensions must be list")
        dimensions = []
    dimension_names = {item.get("name") for item in dimensions if isinstance(item, dict)}
    if dimension_names != REQUIRED_DIMENSIONS:
        errors.append(f"dimension names mismatch: {sorted(str(item) for item in dimension_names)}")
    statuses = {item.get("status") for item in dimensions if isinstance(item, dict)}
    if "UNKNOWN" not in statuses:
        errors.append("scorecard must preserve UNKNOWN external gates")
    if "HUMAN_REVIEW_REQUIRED" not in statuses:
        errors.append("scorecard must require human review for person-impacting use")
    for index, item in enumerate(dimensions):
        if not isinstance(item, dict):
            errors.append(f"dimension[{index}] must be object")
            continue
        _append_missing(errors, f"dimension[{index}]", item, ("id", "name", "status", "gate", "evidence"))

    claims = scorecard.get("public_release_claims", {})
    if not isinstance(claims, dict):
        errors.append("public_release_claims must be object")
        claims = {}
    forbidden = {str(item).lower() for item in claims.get("forbidden", []) if isinstance(item, str)}
    if not FORBIDDEN_PRODUCT_CLAIMS.issubset(forbidden):
        errors.append("public_release_claims.forbidden missing required hard claims")

    from bive.product import product_readiness_status

    runtime = product_readiness_status()
    if runtime.get("overall_status") == "GREEN":
        errors.append("runtime product readiness cannot be GREEN while unknowns remain")
    if runtime.get("release_gate") != "make product-readiness":
        errors.append("runtime status must expose make product-readiness gate")
    if len(runtime.get("blocking_unknowns", [])) < 3:
        errors.append("runtime status must expose blocking unknowns")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "status": "fail" if errors else "pass",
                "model_id": model.get("model_id"),
                "scorecard_id": scorecard.get("scorecard_id"),
                "dimension_count": len(dimensions),
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if errors:
        for error in errors:
            print(f"PRODUCT_READINESS_ERROR {error}", file=sys.stderr)
        return 1
    print("PRODUCT_READINESS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
