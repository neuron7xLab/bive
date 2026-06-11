from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "htmlcov"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}
FORBIDDEN_NAMES = {".coverage", ".dmypy.json", "bive.sqlite3"}
ALLOWED_PREFIXES = {".venv", "build", "dist"}


def is_allowed_generated(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return bool(relative.parts and relative.parts[0] in ALLOWED_PREFIXES)


def main() -> int:
    violations: list[str] = []
    for path in ROOT.rglob("*"):
        if is_allowed_generated(path):
            continue
        if path.is_dir() and path.name in FORBIDDEN_DIRS:
            violations.append(str(path.relative_to(ROOT)))
        if path.is_file() and (path.suffix in FORBIDDEN_SUFFIXES or path.name in FORBIDDEN_NAMES):
            violations.append(str(path.relative_to(ROOT)))
    if violations:
        for violation in sorted(violations):
            print(f"REPO_DIRTY {violation}")
        return 1
    print("REPO_CLEAN_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
