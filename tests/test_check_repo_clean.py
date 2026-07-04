"""Defect-sensitivity proof for the release repo-clean gate.

The prior implementation walked the filesystem against a hard-coded cache
denylist. It had two lie surfaces this suite pins closed:

  * false-negative — a tracked-but-uncommitted source edit, or a stray
    untracked file, passed the gate, so a "clean" release need not correspond
    to any commit;
  * false-positive — a .gitignore'd cache (.mypy_cache/...) tripped the gate,
    making a green release unreachable in any warm environment.

Each test below fails on at least one of those behaviours, so a regression to
the denylist approach is caught.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_repo_clean.py"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(root: Path) -> Path:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "commit.gpgsign", "false")
    (root / ".gitignore").write_text(".mypy_cache/\n__pycache__/\n*.pyc\n")
    (root / "module.py").write_text("value = 1\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    return root


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        capture_output=True,
        text=True,
    )


def test_committed_tree_passes(tmp_path: Path) -> None:
    result = _run(_init_repo(tmp_path))
    assert result.returncode == 0, result.stdout
    assert "REPO_CLEAN_PASS" in result.stdout


def test_gitignored_cache_does_not_trip(tmp_path: Path) -> None:
    """False-positive guard: ignored caches must not block a release."""
    root = _init_repo(tmp_path)
    cache = root / ".mypy_cache"
    cache.mkdir()
    (cache / "cache.json").write_text("{}")
    result = _run(root)
    assert result.returncode == 0, result.stdout
    assert "REPO_CLEAN_PASS" in result.stdout


def test_tracked_modification_trips(tmp_path: Path) -> None:
    """False-negative guard: an uncommitted source edit must block."""
    root = _init_repo(tmp_path)
    (root / "module.py").write_text("value = 2\n")
    result = _run(root)
    assert result.returncode == 1, result.stdout
    assert "REPO_DIRTY" in result.stdout
    assert "module.py" in result.stdout


def test_untracked_nonignored_file_trips(tmp_path: Path) -> None:
    """False-negative guard: a stray untracked file must block."""
    root = _init_repo(tmp_path)
    (root / "secret.env").write_text("TOKEN=leak\n")
    result = _run(root)
    assert result.returncode == 1, result.stdout
    assert "secret.env" in result.stdout


def test_build_output_is_allowed(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    build = root / "build"
    build.mkdir()
    (build / "artifact.whl").write_text("x")
    result = _run(root)
    assert result.returncode == 0, result.stdout


def test_non_git_directory_fails_closed(tmp_path: Path) -> None:
    """Provenance unknowable without git → refuse, never report clean."""
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout
    assert "REPO_CLEAN_INDETERMINATE" in result.stdout
    assert "REPO_CLEAN_PASS" not in result.stdout
