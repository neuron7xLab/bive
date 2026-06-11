from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_MAP = ROOT / "data" / "aos" / "neurocognitive_feature_map.json"
TASK_PROTOCOL = ROOT / "data" / "aos" / "neurocognitive_task_protocol.json"
OUTPUT = ROOT / "artifacts" / "verification" / "NEUROCOGNITIVE_PROTOCOL.json"
REQUIRED_FEATURES = {
    "excitation_inhibition_balance",
    "salience_gating",
    "working_memory_budget",
    "error_monitoring",
    "predictive_reverse_inference",
    "homeostatic_stability",
    "fractal_invariant_recursion",
    "plasticity_calibration",
}
FORBIDDEN_DECORATION = {"singularity", "genius", "magic", "brain-like", "conscious"}


def _load(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain JSON object")
    return data


def main() -> int:
    errors: list[str] = []
    if not FEATURE_MAP.exists():
        errors.append("missing neurocognitive feature map")
        feature_map: dict[str, object] = {}
    else:
        feature_map = _load(FEATURE_MAP)
    if not TASK_PROTOCOL.exists():
        errors.append("missing neurocognitive task protocol")
        task_protocol: dict[str, object] = {}
    else:
        task_protocol = _load(TASK_PROTOCOL)

    features = feature_map.get("features", [])
    if not isinstance(features, list):
        errors.append("features must be list")
        features = []
    feature_ids = {item.get("id") for item in features if isinstance(item, dict)}
    if feature_ids != REQUIRED_FEATURES:
        errors.append(f"feature ids mismatch: {sorted(str(x) for x in feature_ids)}")
    forbidden_claims = feature_map.get("forbidden_claims")
    if not isinstance(forbidden_claims, list) or len(forbidden_claims) < 4:
        errors.append("forbidden_claims must define hard boundaries")
    for feature in features:
        if not isinstance(feature, dict):
            errors.append("feature must be object")
            continue
        for field in ("id", "operational_function", "repository_mechanism", "validator", "test", "failure_mode"):
            if not feature.get(field):
                errors.append(f"feature {feature.get('id')} missing {field}")

    tasks = task_protocol.get("tasks", [])
    if not isinstance(tasks, list):
        errors.append("tasks must be list")
        tasks = []
    task_ids = [item.get("id") for item in tasks if isinstance(item, dict)]
    if len(task_ids) != len(set(task_ids)):
        errors.append("task ids must be unique")
    if len(task_ids) < 8:
        errors.append("at least 8 neurocognitive tasks required")
    valid_classes = {"DEFINE", "RETRIEVE", "ANALYZE", "DESIGN", "IMPLEMENT", "TEST", "AUDIT", "REPAIR", "FINALIZE"}
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("task must be object")
            continue
        if task.get("class") not in valid_classes:
            errors.append(f"task {task.get('id')} has invalid class")
        for field in ("title", "feature", "exact_action", "artifact", "validator", "acceptance", "failure_signal"):
            if not task.get(field):
                errors.append(f"task {task.get('id')} missing {field}")
        text = json.dumps(task, ensure_ascii=False).lower()
        for word in FORBIDDEN_DECORATION:
            if word in text and "failure_signal" not in word:
                errors.append(f"task {task.get('id')} contains decorative term: {word}")
    from bive.neurocognitive import neurocognitive_protocol_status

    status = neurocognitive_protocol_status()
    if status.get("release_gate") != "make neurocognitive-protocol":
        errors.append("runtime status must expose release gate")
    if not status.get("boundary"):
        errors.append("runtime status must expose boundary")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "status": "fail" if errors else "pass",
                "feature_count": len(feature_ids),
                "task_count": len(task_ids),
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
            print(f"NEUROCOGNITIVE_PROTOCOL_ERROR {error}", file=sys.stderr)
        return 1
    print("NEUROCOGNITIVE_PROTOCOL_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
