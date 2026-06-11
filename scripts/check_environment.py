from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import json
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ARTIFACT = ROOT / "artifacts" / "verification" / "environment.json"
MIN_PYTHON = (3, 10)


@dataclass(frozen=True)
class CheckResult:
    name: str
    purpose: str
    status: str
    remediation: str
    version: str | None = None
    detail: str | None = None


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_python() -> CheckResult:
    if sys.version_info >= MIN_PYTHON:
        return CheckResult("python", "Interpreter version", "pass", "", platform.python_version())
    return CheckResult(
        "python",
        "Interpreter version",
        "fail",
        "Use Python 3.10 or newer.",
        platform.python_version(),
    )


def check_import(module: str, purpose: str, extra: str | None = None) -> CheckResult:
    try:
        importlib.import_module(module)
    except ImportError as exc:
        remediation = f'MISSING_DEPENDENCY: {module}. Install with pip install -e ".[dev,api,security]"'
        if extra:
            remediation = f'MISSING_DEPENDENCY: {module}. Install with pip install -e ".[${extra}]"'.replace("[$", "[")
        return CheckResult(module, purpose, "fail", remediation, None, str(exc))
    return CheckResult(module, purpose, "pass", "", _distribution_version(module))


def _read_pyproject() -> dict[str, object]:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # Python < 3.11
        import tomli as tomllib  # type: ignore[no-redef]
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def check_build_backend() -> CheckResult:
    """Validate the declared PEP 517 backend resolves and is importable.

    The project ships no in-tree backend; it relies on the proven, PyPA-maintained
    ``setuptools.build_meta`` backend (see docs/BUILD_BACKEND_DECISION.md).
    """
    purpose = "PEP 517/660 build backend"
    try:
        config = _read_pyproject()
        build_system = config.get("build-system", {})
        backend = build_system.get("build-backend") if isinstance(build_system, dict) else None
    except Exception as exc:  # noqa: BLE001 - surface any parse failure as a gate failure
        return CheckResult("build_backend", purpose, "fail", "UNREADABLE_PYPROJECT: cannot parse pyproject.toml.", None, str(exc))
    if not backend:
        return CheckResult("build_backend", purpose, "fail", "MISSING_BUILD_BACKEND: [build-system] build-backend is not declared.")
    module_name = str(backend).split(":", 1)[0]
    if importlib.util.find_spec(module_name) is None:
        return CheckResult(
            "build_backend",
            purpose,
            "fail",
            f"UNIMPORTABLE_BUILD_BACKEND: '{backend}' is not importable; install build requirements.",
            None,
            str(backend),
        )
    return CheckResult("build_backend", purpose, "pass", "", None, str(backend))


def check_entrypoint(command: str) -> CheckResult:
    found = shutil.which(command)
    if found:
        return CheckResult(command, "Installed console script", "pass", "", None, found)
    return CheckResult(
        command,
        "Installed console script",
        "fail",
        f'MISSING_ENTRYPOINT: {command}. Install with pip install -e ".[dev,api,security]".',
    )


def execute_preflight_audit() -> int:
    checks = [
        check_python(),
        check_import("bive", "Installed BIVE package"),
        check_import("pydantic", "Core data modeling layer"),
        check_import("fastapi", "HTTP API infrastructure layer", "api"),
        check_import("uvicorn", "HTTP API server runtime", "api"),
        check_import("jsonschema", "JSON contract validation layer", "dev"),
        check_import("pytest", "Test release gate", "dev"),
        check_import("ruff", "Lint release gate", "dev"),
        check_import("mypy", "Static type release gate", "dev"),
        check_import("pip_audit", "Dependency vulnerability audit", "security"),
        check_build_backend(),
        check_entrypoint("bive"),
        check_entrypoint("bive-api"),
        check_entrypoint("bive-aos"),
        check_entrypoint("bive-cognitive-control"),
    ]
    status = "pass" if all(item.status == "pass" for item in checks) else "fail"
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "status": status,
        "python": sys.version,
        "platform": platform.platform(),
        "checks": [asdict(item) for item in checks],
    }
    ARTIFACT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    print("[BIVE PREFLIGHT] System dependency inventory")
    for item in checks:
        if item.status == "pass":
            suffix = f" version={item.version}" if item.version else ""
            if item.detail and not item.version:
                suffix = f" detail={item.detail}"
            print(f"  [PASS] {item.name}: {item.purpose}{suffix}")
        else:
            print(f"  [FAIL] {item.name}: {item.remediation}", file=sys.stderr)
    if status != "pass":
        print(f"[BIVE PREFLIGHT] blocked; see {ARTIFACT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    print(f"[BIVE PREFLIGHT] pass; wrote {ARTIFACT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(execute_preflight_audit())
