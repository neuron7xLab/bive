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
    "dev.in": {"pytest", "pytest-cov", "ruff", "mypy", "jsonschema", "build", "httpx", "pip-tools"},
    "security.in": {"pip-audit", "cyclonedx-bom", "pip-licenses", "bandit"},
    "prod.in": {"core.in", "api.in"},
    "core.txt": {"pydantic"},
    "api.txt": {"fastapi", "uvicorn", "starlette"},
    "dev.txt": {"pytest", "pytest-cov", "ruff", "mypy", "jsonschema", "build", "httpx", "pip-tools"},
    "security.txt": {"pip-audit", "cyclonedx-bom", "pip-licenses", "bandit"},
    "prod.txt": {"api.txt"},
}

REQUIRED_CONSTRAINT_PINS = {
    "pydantic",
    "fastapi",
    "starlette",
    "uvicorn",
    "jsonschema",
    "pytest",
    "ruff",
    "mypy",
    "build",
    "pytest-cov",
    "coverage",
    "httpx",
    "bandit",
    "pip-audit",
    "cyclonedx-bom",
    "pip-licenses",
    "pip-tools",
}

STRICT_ALIGNMENT_GROUPS = {
    "pydantic": ("requirements/core.txt", "constraints/py310.txt"),
    "fastapi": ("requirements/api.txt", "constraints/py310.txt"),
    "starlette": ("requirements/api.txt", "constraints/py310.txt"),
    "uvicorn": ("requirements/api.txt", "constraints/py310.txt"),
    "jsonschema": ("requirements/dev.txt", "constraints/py310.txt"),
    "pytest": ("requirements/dev.txt", "constraints/py310.txt"),
    "ruff": ("requirements/dev.txt", "constraints/py310.txt"),
    "mypy": ("requirements/dev.txt", "constraints/py310.txt"),
    "build": ("requirements/dev.txt", "constraints/py310.txt"),
    "pytest-cov": ("requirements/dev.txt", "constraints/py310.txt"),
    "httpx": ("requirements/dev.txt", "constraints/py310.txt"),
    "pip-tools": ("requirements/dev.txt", "constraints/py310.txt"),
    "bandit": ("requirements/security.txt", "constraints/py310.txt"),
    "pip-audit": ("requirements/security.txt", "constraints/py310.txt"),
    "cyclonedx-bom": ("requirements/security.txt", "constraints/py310.txt"),
    "pip-licenses": ("requirements/security.txt", "constraints/py310.txt"),
}

REQUIRED_PYPROJECT_FRAGMENTS = {
    'dependencies = ["pydantic==2.13.4"]',
    'fastapi==0.136.3',
    'starlette==1.3.0',
    'uvicorn==0.49.0',
    'pip-audit==2.10.1',
    }

PIN_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;#]+)")


def _normalize_package_name(value: str) -> str:
    return value.lower().replace("_", "-")


def _normalize_package(line: str) -> str | None:
    text = line.strip()
    if not text or text.startswith("#") or text.startswith("-"):
        return None
    match = re.match(r"([A-Za-z0-9_.-]+)", text)
    if not match:
        return None
    return _normalize_package_name(match.group(1))


def _read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"DEPENDENCY_CONTRACT_FAIL missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _parse_exact_pins(relative_path: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in _read(ROOT / relative_path).splitlines():
        text = line.strip()
        if not text or text.startswith("#") or text.startswith("-"):
            continue
        match = PIN_PATTERN.match(text)
        if match:
            package = _normalize_package_name(match.group(1))
            version = match.group(2)
            if package in pins:
                raise SystemExit(
                    f"DEPENDENCY_CONTRACT_FAIL duplicate pin for {package} in {relative_path}"
                )
            pins[package] = version
    return pins


def _artifact_payload(
    pinned: dict[str, str], requirement_packages: dict[str, list[str]]
) -> dict[str, object]:
    return {
        "status": "pass",
        "requirement_files": sorted(REQUIRED_REQUIREMENT_FILES),
        "constraint_pins": sorted(pinned),
        "strict_alignment_groups": {
            package: list(paths) for package, paths in sorted(STRICT_ALIGNMENT_GROUPS.items())
        },
        "requirement_packages": requirement_packages,
    }


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
        match = PIN_PATTERN.match(line.strip())
        if not match:
            errors.append(f"constraints/py310.txt has non-exact pin: {line}")
            continue
        if package in pinned:
            errors.append(f"constraints/py310.txt duplicates pin: {package}")
        pinned[package] = match.group(2)

    missing_pins = sorted(REQUIRED_CONSTRAINT_PINS - set(pinned))
    if missing_pins:
        errors.append(f"constraints/py310.txt missing pins: {missing_pins}")

    pin_cache = {relative: _parse_exact_pins(relative) for paths in STRICT_ALIGNMENT_GROUPS.values() for relative in paths}
    for package, paths in sorted(STRICT_ALIGNMENT_GROUPS.items()):
        observed = {relative: pin_cache[relative].get(package) for relative in paths}
        missing = [relative for relative, version in observed.items() if version is None]
        if missing:
            errors.append(f"{package} missing from aligned files: {missing}")
            continue
        versions = {version for version in observed.values() if version is not None}
        if len(versions) != 1:
            rendered = ", ".join(f"{relative}={version}" for relative, version in observed.items())
            errors.append(f"{package} lockfile synchronicity split detected: {rendered}")

    if errors:
        raise SystemExit("DEPENDENCY_CONTRACT_FAIL\n" + "\n".join(f"- {e}" for e in errors))

    payload = _artifact_payload(pinned, requirement_packages)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DEPENDENCY_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
