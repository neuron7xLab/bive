from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "verification" / "TEST_ARCHITECTURE.json"
REQUIRED_TEST_FILES = {
    "tests/test_api.py",
    "tests/test_api_operational_contract.py",
    "tests/test_api_security_runtime.py",
    "tests/test_schema_contract.py",
    "tests/test_dynamic_environment_probe.py",
    "tests/test_storage_operational_contract.py",
    "tests/test_adapters_contract.py",
    "tests/test_dependency_contracts.py",
    "tests/test_automation_contract.py",
    "tests/test_bibliography_contract.py",
    "tests/test_release_gate_contract.py",
    "tests/test_behavioral_invariants.py",
    "tests/test_microsoft_hardening_contract.py",
    "tests/test_aos_kernel.py",
    "tests/test_aos_api_contract.py",
}
MIN_TEST_FUNCTIONS = 70
REQUIRED_ASSERT_TOKENS = {
    "Traceback",
    "authentication_required",
    "too_many_segments",
    "DYNAMIC_ENVIRONMENT_PROBE_PASS",
    "DEPENDENCY_CONTRACT_PASS",
    "AUTOMATION_CONTRACT_PASS",
    "BIBLIOGRAPHY_PASS",
    "THREAT_MODEL_PASS",
    "MICROSOFT_REST_CONTRACT_PASS",
    "OPERATIONAL_EXCELLENCE_PASS",
    "AOS_KERNEL_PASS",
}


def _test_functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]


def main() -> int:
    errors: list[str] = []
    for relative in sorted(REQUIRED_TEST_FILES):
        if not (ROOT / relative).exists():
            errors.append(f"missing required test file: {relative}")

    tests: dict[str, list[str]] = {}
    joined = ""
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        functions = _test_functions(path)
        tests[str(path.relative_to(ROOT))] = functions
        joined += path.read_text(encoding="utf-8") + "\n"

    total = sum(len(items) for items in tests.values())
    if total < MIN_TEST_FUNCTIONS:
        errors.append(f"test function count {total} < {MIN_TEST_FUNCTIONS}")
    for token in sorted(REQUIRED_ASSERT_TOKENS):
        if token not in joined:
            errors.append(f"test suite missing assertion token: {token}")

    if errors:
        raise SystemExit("TEST_ARCHITECTURE_FAIL\n" + "\n".join(f"- {e}" for e in errors))

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps({"status": "pass", "test_functions": total, "files": tests}, indent=2),
        encoding="utf-8",
    )
    print("TEST_ARCHITECTURE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
