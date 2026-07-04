from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Build outputs may legitimately exist untracked in the tree; everything else
# must correspond to committed state. These are also .gitignore'd, so they only
# matter if a consumer un-ignores them — keep the allowance explicit either way.
ALLOWED_PREFIXES: tuple[str, ...] = ("build/", "dist/", ".venv/")


def _porcelain(root: Path) -> list[str]:
    """Return non-empty `git status --porcelain` lines (ignored files excluded).

    Fails closed: if git cannot establish state (not a repo, git missing), the
    provenance of the tree is unknowable, so we refuse rather than report clean.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--ignored=no"],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except OSError as exc:  # git binary unavailable
        print(f"REPO_CLEAN_INDETERMINATE git unavailable: {exc}")
        raise SystemExit(1) from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit={result.returncode}"
        print(f"REPO_CLEAN_INDETERMINATE git status failed: {detail}")
        raise SystemExit(1)
    return [line for line in result.stdout.splitlines() if line.strip()]


def _path_of(entry: str) -> str:
    """Extract the path from a porcelain entry, handling renames and quoting."""
    path = entry[3:] if len(entry) > 3 else entry
    if " -> " in path:  # renamed: 'R  old -> new'
        path = path.split(" -> ", 1)[1]
    return path.strip().strip('"')


def evaluate(root: Path) -> list[str]:
    """Return violation lines; empty list means the tree matches committed state."""
    violations: list[str] = []
    for entry in _porcelain(root):
        if any(_path_of(entry).startswith(prefix) for prefix in ALLOWED_PREFIXES):
            continue
        violations.append(entry)
    return violations


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else ROOT
    violations = evaluate(root)
    if violations:
        for violation in sorted(violations):
            print(f"REPO_DIRTY {violation}")
        return 1
    print("REPO_CLEAN_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
