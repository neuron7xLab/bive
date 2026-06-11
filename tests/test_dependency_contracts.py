from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_script(relative: str) -> ModuleType:
    path = Path(relative)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def test_dependency_contract_script_passes(capsys) -> None:  # type: ignore[no-untyped-def]
    main = _load_script("scripts/validate_dependency_contracts.py").main
    assert main() == 0
    assert "DEPENDENCY_CONTRACT_PASS" in capsys.readouterr().out


def test_dependency_contract_artifact_records_constraint_pins() -> None:
    main = _load_script("scripts/validate_dependency_contracts.py").main
    assert main() == 0
    data = json.loads(Path("artifacts/verification/DEPENDENCY_CONTRACT_VALIDATION.json").read_text())
    assert data["status"] == "pass"
    assert "fastapi" in data["constraint_pins"]
    assert "pip-audit" in data["constraint_pins"]
    for filename in ("core.txt", "api.txt", "prod.txt", "dev.txt", "security.txt"):
        assert filename in data["requirement_files"]


def test_dependency_files_have_separate_runtime_surfaces() -> None:
    assert "pydantic" in Path("requirements/core.in").read_text()
    assert "fastapi" in Path("requirements/api.in").read_text()
    assert "pytest" in Path("requirements/dev.in").read_text()
    assert "pip-audit" in Path("requirements/security.in").read_text()
    assert "pydantic==" in Path("requirements/core.txt").read_text()
    assert "fastapi==" in Path("requirements/api.txt").read_text()


def test_constraints_are_exact_pins() -> None:
    lines = [x.strip() for x in Path("constraints/py310.txt").read_text().splitlines()]
    pins = [x for x in lines if x and not x.startswith("#")]
    assert pins
    assert all("==" in line for line in pins)


def test_pyproject_matches_canonical_runtime_pins() -> None:
    text = Path("pyproject.toml").read_text()
    assert "pydantic==2.13.4" in text
    assert "fastapi==0.136.3" in text
    assert "starlette==1.3.0" in text
    assert "uvicorn==0.49.0" in text


def test_dependency_policy_is_documented() -> None:
    text = Path("docs/DEPENDENCY_POLICY.md").read_text()
    assert "make dependency-contracts" in text
    assert "UNKNOWN" in text
