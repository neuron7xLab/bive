from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "aos" / "cognitive_control_plane.json"
OUTPUT = ROOT / "artifacts" / "verification" / "COGNITIVE_CONTROL_PLANE.json"
REQUIRED_AGENTS = {
    "intent_compiler",
    "boundary_detector",
    "contract_engineer",
    "verification_engineer",
    "critical_auditor",
    "repair_optimizer",
}
REQUIRED_LEVELS = {"intent", "boundary", "contract", "verification", "release"}
REQUIRED_INVARIANTS = {
    "input_defined",
    "output_defined",
    "failure_path_defined",
    "evidence_required",
    "human_gate_when_high_risk",
}


def main() -> int:
    errors: list[str] = []
    if not CONTRACT.exists():
        errors.append("missing data/aos/cognitive_control_plane.json")
        data: object = {}
    else:
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        errors.append("contract must be object")
        data = {}
    agents = data.get("agents")
    agent_names = {item.get("name") for item in agents if isinstance(item, dict)} if isinstance(agents, list) else set()
    if agent_names != REQUIRED_AGENTS:
        errors.append(f"agents mismatch: {sorted(agent_names)}")
    levels = set(data.get("fractal_levels", [])) if isinstance(data.get("fractal_levels"), list) else set()
    if levels != REQUIRED_LEVELS:
        errors.append(f"fractal levels mismatch: {sorted(levels)}")
    invariants = set(data.get("recursive_invariants", [])) if isinstance(data.get("recursive_invariants"), list) else set()
    if invariants != REQUIRED_INVARIANTS:
        errors.append(f"recursive invariants mismatch: {sorted(invariants)}")
    bounds = data.get("weight_bounds")
    if not isinstance(bounds, dict):
        errors.append("missing weight bounds")
    else:
        if bounds.get("excitation_min") != 0.0 or bounds.get("excitation_max") != 1.0:
            errors.append("excitation bounds must be [0.0, 1.0]")
        if bounds.get("inhibition_min") != 0.0 or bounds.get("inhibition_max") != 1.0:
            errors.append("inhibition bounds must be [0.0, 1.0]")
        if not isinstance(bounds.get("target_excitation_range"), list):
            errors.append("target excitation range required")
        if not isinstance(bounds.get("target_inhibition_range"), list):
            errors.append("target inhibition range required")
    targets = data.get("reverse_inference_targets")
    if not isinstance(targets, dict) or "GREEN" not in targets or "BLOCKED" not in targets:
        errors.append("reverse inference targets must include GREEN and BLOCKED")

    from bive.cognitive_control import cognitive_control_status, orchestrate_request

    sample = orchestrate_request("Repair repository gates without production side effects")
    risky = orchestrate_request("Deploy to production and rotate customer tokens")
    if sample.mode.value not in {"EXECUTE_BOUNDED", "SPECIFY_ONLY"}:
        errors.append("low/medium sample should not require human gate")
    if risky.mode.value != "HUMAN_GATE":
        errors.append("high-risk request must route to HUMAN_GATE")
    if len(sample.agent_votes) != len(REQUIRED_AGENTS):
        errors.append("sample must include all agent votes")
    if not all(check.passed for check in sample.fractal_checks):
        errors.append("sample fractal checks must pass")
    status = cognitive_control_status()
    if status.get("release_gate") != "make cognitive-control":
        errors.append("status must expose release gate")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "status": "fail" if errors else "pass",
                "agent_count": len(agent_names),
                "fractal_level_count": len(levels),
                "sample_mode": sample.mode.value,
                "risky_mode": risky.mode.value,
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
            print(f"COGNITIVE_CONTROL_ERROR {error}", file=sys.stderr)
        return 1
    print("COGNITIVE_CONTROL_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
