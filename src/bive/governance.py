from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    details: str

    def line(self) -> str:
        return f"{'PASS' if self.passed else 'FAIL'} {self.name}: {self.details}"


def check_required_files(repo: Path) -> list[GateResult]:
    required = [
        "README.md",
        "pyproject.toml",
        "Makefile",
        "src/bive/api.py",
        "src/bive/web/index.html",
        "schemas/verification_report.schema.json",
        "docs/ARCHITECTURE.md",
        "docs/API.md",
        ".github/workflows/ci.yml",
        "Dockerfile",
        "docker-compose.yml",
    ]
    return [GateResult(f"file:{p}", (repo / p).exists(), p) for p in required]


def evaluate_repo_surface(repo: str | Path) -> list[GateResult]:
    root = Path(repo)
    results = check_required_files(root)
    readme = (
        (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    )
    results.append(
        GateResult(
            "readme-no-verdict-field",
            "liar=true" not in readme.lower() and "guilty=true" not in readme.lower(),
            "README avoids machine-verdict fields",
        )
    )
    return results
