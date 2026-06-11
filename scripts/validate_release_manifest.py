from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENIED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "htmlcov",
    "build",
    "dist",
}
DENIED_SUFFIXES = (".pyc", ".pyo", ".sqlite3", ".db")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest_path = ROOT / "ARTIFACT_MANIFEST.json"
    if not manifest_path.exists():
        print("MANIFEST_ERROR missing ARTIFACT_MANIFEST.json", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for item in manifest.get("files", []):
        rel = item.get("path")
        if not isinstance(rel, str):
            errors.append("file entry without path")
            continue
        path = ROOT / rel
        parts = Path(rel).parts
        if any(
            part in DENIED_PARTS or part.endswith(".egg-info") for part in parts
        ) or rel.endswith(DENIED_SUFFIXES):
            errors.append(f"forbidden file in manifest: {rel}")
            continue
        if not path.exists():
            errors.append(f"missing file: {rel}")
            continue
        if item.get("bytes") != path.stat().st_size:
            errors.append(f"size mismatch: {rel}")
        if item.get("sha256") != sha256(path):
            errors.append(f"sha256 mismatch: {rel}")
    if errors:
        for error in errors:
            print(f"MANIFEST_ERROR {error}", file=sys.stderr)
        return 1
    print("MANIFEST_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
