from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "prompts" / "AOS_PROMPT_KERNEL_v1.0.txt"
TASKS = ROOT / "evals" / "aos_eval_tasks.json"
SCORE = ROOT / "evals" / "aos_score_schema.json"
CONTRACT = ROOT / "data" / "aos" / "aos_kernel_contract.json"
OUTPUT = ROOT / "artifacts" / "verification" / "AOS_KERNEL_VALIDATION.json"

REQUIRED_PROMPT_MARKERS = [
    "SECTION 1 — SYSTEM PROMPT",
    "SECTION 5 — EPISTEMIC RULES",
    "SECTION 10 — SECURITY AND PERMISSION MODEL",
    "SECTION 14 — AUTOMATION-OF-AUTOMATION ARCHITECTURE",
    "SECTION 16 — EVAL HARNESS",
    "SECTION 21 — CANONICAL FINAL LAW",
]
REQUIRED_TASK_FIELDS = {
    "id",
    "category",
    "user_request",
    "risk",
    "expected_status",
    "required_output_fields",
    "must_include",
    "must_not_include",
}
REQUIRED_SCORE_METRICS = {
    "intent_fidelity",
    "operational_specificity",
    "contract_completeness",
    "verification_strength",
    "failure_coverage",
    "context_efficiency",
    "safety_boundary",
    "reuse_value",
    "production_fit",
    "falsifiability",
}
REQUIRED_MODULES = {
    "intent_compiler",
    "process_modeler",
    "automation_boundary_engine",
    "tool_contract_generator",
    "workflow_generator",
    "sandbox_executor",
    "verifier",
    "repair_engine",
    "template_registry",
    "governance_engine",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    if not PROMPT.exists():
        errors.append("missing prompt kernel")
        prompt_text = ""
    else:
        prompt_text = PROMPT.read_text(encoding="utf-8")
        for marker in REQUIRED_PROMPT_MARKERS:
            if marker not in prompt_text:
                errors.append(f"prompt missing marker: {marker}")
        if len(prompt_text.split()) < 1200:
            errors.append("prompt kernel is too short to encode the canonical contract")

    tasks_data = load_json(TASKS) if TASKS.exists() else {}
    tasks = tasks_data.get("tasks") if isinstance(tasks_data, dict) else None
    if not isinstance(tasks, list):
        errors.append("eval tasks must contain a tasks list")
        tasks = []
    if len(tasks) < 20:
        errors.append("eval harness must define at least 20 tasks")
    ids: set[str] = set()
    categories: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"task {index} must be object")
            continue
        missing = REQUIRED_TASK_FIELDS - set(task)
        if missing:
            errors.append(f"task {index} missing fields: {sorted(missing)}")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            errors.append(f"task {index} missing id")
        elif task_id in ids:
            errors.append(f"duplicate task id: {task_id}")
        else:
            ids.add(task_id)
        category = task.get("category")
        if isinstance(category, str):
            categories.add(category)
        if task.get("risk") not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            errors.append(f"task {task_id} has invalid risk")
        if task.get("expected_status") not in {"GREEN", "YELLOW", "RED", "UNKNOWN", "BLOCKED", "HUMAN_REVIEW_REQUIRED"}:
            errors.append(f"task {task_id} has invalid expected_status")
    if len(categories) < 15:
        errors.append("eval harness must cover at least 15 categories")

    score_data = load_json(SCORE) if SCORE.exists() else {}
    metrics = score_data.get("metrics") if isinstance(score_data, dict) else None
    metric_names = {item.get("name") for item in metrics if isinstance(item, dict)} if isinstance(metrics, list) else set()
    if metric_names != REQUIRED_SCORE_METRICS:
        errors.append("score schema metrics do not match AOS rubric")

    contract_data = load_json(CONTRACT) if CONTRACT.exists() else {}
    modules = contract_data.get("required_modules") if isinstance(contract_data, dict) else None
    module_names = set(modules) if isinstance(modules, list) else set()
    if module_names != REQUIRED_MODULES:
        errors.append("kernel contract missing required automation-of-automation modules")
    pipeline = contract_data.get("canonical_pipeline") if isinstance(contract_data, dict) else None
    if not isinstance(pipeline, list) or len(pipeline) < 10:
        errors.append("kernel contract canonical pipeline is incomplete")

    payload = {
        "status": "fail" if errors else "pass",
        "prompt_bytes": PROMPT.stat().st_size if PROMPT.exists() else 0,
        "eval_task_count": len(tasks),
        "eval_category_count": len(categories),
        "score_metric_count": len(metric_names),
        "required_module_count": len(module_names),
        "errors": errors,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        for error in errors:
            print(f"AOS_KERNEL_ERROR {error}", file=sys.stderr)
        return 1
    print("AOS_KERNEL_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
