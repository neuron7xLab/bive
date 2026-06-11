from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_DIR = ROOT / "requirements"
CONSTRAINTS_FILE = ROOT / "constraints" / "py310.txt"
ARTIFACT = ROOT / "artifacts" / "verification" / "DEPENDENCY_CONTRACT_VALIDATION.json"

REQUIRED_REQUIREMENT_FILES = {
    "core.in": {"pydantic"},
    "api.in": {"fastapi", "uvicorn"},
    "dev.in": {"pytest", "pytest-cov", "ruff", "mypy", "jsonschema", "httpx", "bandit", "build", "pip-tools"},
    "security.in": {"pip-audit", "cyclonedx-bom", "pip-licenses", "bandit"},
    "prod.in": {"core.in", "api.in"},
    "core.txt": {"pydantic"},
    "api.txt": {"fastapi", "uvicorn", "starlette"},
    "dev.txt": {"pytest", "pytest-cov", "ruff", "mypy", "jsonschema", "httpx", "bandit", "build", "pip-tools"},
    "security.txt": {"pip-audit", "cyclonedx-bom", "pip-licenses", "bandit"},
    "prod.txt": {"api.txt"},
}
REQUIRED_CONSTRAINT_PINS = {
    "pydantic",
    "pytest",
    "pytest-cov",
    "coverage",
    "ruff",
    "mypy",
    "jsonschema",
    "httpx",
    "bandit",
    "build",
    "pip-audit",
    "pip-licenses",
    "fastapi",
    "starlette",
    "uvicorn",
    "cyclonedx-bom",
}
REQUIRED_PYPROJECT_FRAGMENTS = {
    'dependencies = ["pydantic>=2.6,<3"]',
    'fastapi>=0.110,<1',
    'uvicorn[standard]>=0.27,<1',
    'pip-audit>=2.7,<3',
    'pip-tools>=7,<8',
}


def _normalize_package(line: str) -> str | None:
    text = line.strip()
    if not text or text.startswith("#") or text.startswith("-"):
        return None
    match = re.match(r"([A-Za-z0-9_.-]+)", text)
    if not match:
        return None
    return match.group(1).lower().replace("_", "-")


def _read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"DEPENDENCY_CONTRACT_FAIL missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    pyproject = _read(ROOT / "pyproject.toml")
    errors: list[str] = []
    for fragment in REQUIRED_PYPROJECT_FRAGMENTS:
        if fragment not in pyproject:
            errors.append(f"pyproject missing fragment: {fragment}")

    requirement_packages: dict[str, list[str]] = {}
    for filename, required_tokens in REQUIRED_REQUIREMENT_FILES.items():
        path = REQUIREMENTS_DIR / filename
        content = _read(path)
        lowered = content.lower()
        for token in required_tokens:
            if token.lower() not in lowered:
                errors.append(f"requirements/{filename} missing token {token}")
        packages = sorted(filter(None, (_normalize_package(line) for line in content.splitlines())))
        requirement_packages[filename] = packages
        for line in content.splitlines():
            package = _normalize_package(line)
            if package is not None and ">=" not in line and "==" not in line:
                errors.append(f"requirements/{filename} has unbounded dependency line: {line}")
            if filename.endswith(".txt") and package is not None and "==" not in line:
                errors.append(f"requirements/{filename} must use exact pins, got: {line}")

    constraints = _read(CONSTRAINTS_FILE)
    pinned: dict[str, str] = {}
    for line in constraints.splitlines():
        package = _normalize_package(line)
        if package is None:
            continue
        if "==" not in line:
            errors.append(f"constraints/py310.txt has non-exact pin: {line}")
            continue
        if package in pinned:
            errors.append(f"constraints/py310.txt duplicates pin: {package}")
        pinned[package] = line.strip()

    missing_pins = sorted(REQUIRED_CONSTRAINT_PINS - set(pinned))
    if missing_pins:
        errors.append(f"constraints/py310.txt missing pins: {missing_pins}")

    if errors:
        raise SystemExit("DEPENDENCY_CONTRACT_FAIL\n" + "\n".join(f"- {e}" for e in errors))

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {
                "status": "pass",
                "requirement_files": sorted(REQUIRED_REQUIREMENT_FILES),
                "constraint_pins": sorted(pinned),
                "requirement_packages": requirement_packages,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("DEPENDENCY_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
