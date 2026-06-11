from __future__ import annotations

import argparse
import json
from pathlib import Path

from .governance import evaluate_repo_surface
from .validation import validate_report_dict


def iter_py(repo: Path) -> list[Path]:
    return [p for p in repo.rglob("*.py") if ".venv" not in p.parts and "build" not in p.parts]


def compile_python(repo: Path) -> list[str]:
    errors: list[str] = []
    for path in iter_py(repo):
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, ValueError) as exc:
            errors.append(f"python compile failed: {path}: {exc}")
    return errors


def validate_json_artifacts(repo: Path) -> list[str]:
    errors: list[str] = []
    for path in repo.rglob("*.json"):
        if any(part in {".venv", "build", "dist"} for part in path.parts):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"json parse failed: {path}: {exc}")
            continue
        if isinstance(data, dict) and "final_assessment" in data and "hypotheses" in data:
            errors.extend(f"{path}: {e}" for e in validate_report_dict(data))
    return errors


def check_docs(repo: Path) -> list[str]:
    required = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/FORMAL_SPEC.md",
        "docs/BIBLIOGRAPHY.md",
        "docs/PR_MERGE_PROTOCOL.md",
        "docs/LIMITATIONS.md",
    ]
    return [f"missing required doc: {p}" for p in required if not (repo / p).exists()]


def run(repo: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(compile_python(repo))
    errors.extend(validate_json_artifacts(repo))
    errors.extend(check_docs(repo))
    errors.extend(item.line() for item in evaluate_repo_surface(repo) if not item.passed)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(prog="bive-pr-check")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    errors = run(Path(args.repo).resolve())
    if errors:
        print("PR_GATE_FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("PR_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
