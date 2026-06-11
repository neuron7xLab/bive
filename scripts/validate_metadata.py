from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 ships no stdlib tomllib
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    project = tomllib.loads(read("pyproject.toml"))["project"]
    name = project["name"]
    version = project["version"]
    errors: list[str] = []

    init_text = read("src/bive/__init__.py")
    if f'__version__ = "{version}"' not in init_text:
        errors.append("src/bive/__init__.py __version__ does not match pyproject version")

    readme = read("README.md")
    if f"# BIVE v{version}" not in readme:
        errors.append("README heading does not match pyproject version")
    if "v0.3.0" in readme or "20 passed" in readme:
        errors.append("README contains stale version/test-count text")

    source_registry = read("SOURCE_REGISTRY.yaml")
    if not re.search(rf"^version:\s*{re.escape(version)}\s*$", source_registry, re.M):
        errors.append("SOURCE_REGISTRY.yaml version does not match pyproject version")

    if (ROOT / "ARTIFACT_MANIFEST.json").exists():
        manifest = json.loads(read("ARTIFACT_MANIFEST.json"))
        if manifest.get("name") != name:
            errors.append("ARTIFACT_MANIFEST name does not match pyproject")
        if manifest.get("version") != version:
            errors.append("ARTIFACT_MANIFEST version does not match pyproject")

    if errors:
        for error in errors:
            print(f"METADATA_ERROR {error}", file=sys.stderr)
        return 1
    print("METADATA_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
