from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
DENY_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "htmlcov",
    "build",
    "dist",
    "bive.egg-info",
}
DENY_SUFFIXES = {".pyc", ".pyo", ".sqlite3", ".db"}
DENY_NAMES = {".coverage"}
GENERATED_BUT_ALLOWED = {
    "ARTIFACT_MANIFEST.json",
    "REPO_TREE.txt",
    "docs/openapi.json",
    "artifacts/verification/PATCH_SUMMARY.md",
    "artifacts/verification/PATCHED_FILE_INVENTORY.txt",
    "artifacts/verification/PRODUCTIZATION_SUMMARY.md",
    "artifacts/verification/INDEPENDENT_GATE_EVIDENCE.md",
    "artifacts/verification/STAGE4_PRODUCT_DESIGN_SUMMARY.md",
    "artifacts/verification/STAGE5_CODE_TEST_HARDENING_SUMMARY.md",
    "artifacts/verification/STAGE5_INDEPENDENT_GATES.log",
    "artifacts/verification/STAGE5_INDEPENDENT_GATES_CONTINUED.log",
    "artifacts/verification/STAGE5_INDEPENDENT_GATES_FINAL.log",
    "artifacts/verification/STAGE6_DYNAMIC_SCIENCE_PACKAGING_SUMMARY.md",
    "artifacts/verification/STAGE6_INDEPENDENT_GATES.log",
    "artifacts/verification/STAGE6_INDEPENDENT_GATES_FINAL.log",
    # NOTE: VERIFY_RELEASE.log is intentionally NOT pinned. It is rewritten on every
    # `make verify-release` run and embeds non-reproducible subprocess output (random
    # pip temp paths and the per-build wheel sha256), so a byte-stable hash is
    # impossible. Pinning it made the manifest gate self-referentially flaky.
    "artifacts/verification/DOCKER_RUNTIME_STAGE6_ATTEMPT.log",
    "artifacts/verification/SCIENCE_REGISTRY_VALIDATION.json",
    "artifacts/verification/DYNAMIC_ENVIRONMENT_PROBE.json",
    "artifacts/verification/DOCKER_RUNTIME_ATTEMPT.log",
    "artifacts/security/pip-audit.attempt.log",
    "artifacts/security/pip-audit.stage6.attempt.log",
    "artifacts/verification/STAGE7_ENGINEERING_AUTOMATION_SUMMARY.md",
    "artifacts/verification/DEPENDENCY_CONTRACT_VALIDATION.json",
    "artifacts/verification/TEST_ARCHITECTURE.json",
    "artifacts/verification/AUTOMATION_CONTRACT.json",
    "artifacts/verification/BIBLIOGRAPHY_VALIDATION.json",
    "artifacts/security/pip-audit.stage7.attempt.log",
    "artifacts/security/licenses.stage7.json",
    "artifacts/verification/NEUROCOGNITIVE_PROTOCOL.json",
    "artifacts/verification/PRODUCT_READINESS.json",
    "artifacts/verification/STAGE11_INDUSTRIAL_PRODUCT_SUMMARY.md",
    "artifacts/benchmarks/pipeline.json",
}


def include(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if not path.is_file():
        return False
    if any(
        part in DENY_PARTS or part.endswith(".egg-info") for part in path.relative_to(ROOT).parts
    ):
        return False
    if path.name in DENY_NAMES:
        return False
    if any(path.name.endswith(suffix) for suffix in DENY_SUFFIXES):
        return False
    return not (
        rel.startswith("artifacts/")
        and rel not in GENERATED_BUT_ALLOWED
        and not rel.startswith("artifacts/demo_report")
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if include(path):
            rel = path.relative_to(ROOT).as_posix()
            if rel in {"ARTIFACT_MANIFEST.json", "PRODUCT_SYSTEM_INDEX.json", "REPO_TREE.txt"}:
                continue
            rows.append({"path": rel, "sha256": sha256(path), "bytes": path.stat().st_size})
    return rows


def build_manifest() -> dict[str, object]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    files = collect_files()
    payload = {
        "name": project["name"],
        "version": project["version"],
        "artifact": f"{project['name']}_productized_repo_v{project['version'].replace('.', '_')}",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "scope": "open-source productized evidence-first transcript verification engine",
        "release_state": "machine-assisted; dependency CVE and Docker runtime gates require external environment when unavailable",
        "verification_command": "make verify-release",
        "file_count": len(files),
        "files": files,
    }
    return payload


def write_outputs(manifest: dict[str, object]) -> None:
    files = manifest["files"]
    assert isinstance(files, list)
    (ROOT / "ARTIFACT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / "REPO_TREE.txt").write_text(
        "\n".join(str(item["path"]) for item in files if isinstance(item, dict)) + "\n",
        encoding="utf-8",
    )
    index = {
        "name": manifest["name"],
        "version": manifest["version"],
        "entrypoints": ["bive", "bive-api", "bive-pr-check", "bive-aos"],
        "primary_gates": [
            "make verify",
            "make verify-release",
            "make dependency-contracts",
            "make test-architecture",
            "make automation-contract",
            "make aos-kernel",
            "make bibliography",
            "make frontend-quality",
            "make wheel-smoke",
            "make product-readiness",
        ],
        "docs": [
            "README.md",
            "docs/OPERATIONS.md",
            "docs/SECURITY_MODEL.md",
            "docs/RELEASE_GATES.md",
            "docs/DESIGN_SYSTEM.md",
            "docs/BACKEND_FRONTEND_CONTRACT.md",
            "docs/UI_SPEC.md",
            "docs/SYSTEM_DESIGN_PRINCIPLES.md",
            "docs/DEPENDENCY_POLICY.md",
            "docs/TEST_STRATEGY.md",
            "docs/AUTOMATION_PLAYBOOK.md",
            "docs/ENGINEERING_VALIDATION.md",
            "docs/AOS_PROMPT_OS.md",
            "docs/AUTOMATION_OF_AUTOMATION_KERNEL.md",
            "docs/PRODUCT_OPERATING_MODEL.md",
            "docs/INDUSTRIAL_RELEASE_PACKAGE.md",
            "docs/PRODUCT_MANAGER_READINESS.md",
        ],
        "schemas": [
            "schemas/transcript_analyze_request.schema.json",
            "schemas/verification_report.schema.json",
        ],
        "safety_boundary": "reviewable evidence only; no automatic person-level lie/guilt verdicts",
        "manifest_sha256": sha256(ROOT / "ARTIFACT_MANIFEST.json"),
    }
    (ROOT / "PRODUCT_SYSTEM_INDEX.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = build_manifest()
    if args.check:
        current = json.loads((ROOT / "ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
        comparable_current = dict(current)
        comparable_manifest = dict(manifest)
        comparable_current.pop("generated_at_utc", None)
        comparable_manifest.pop("generated_at_utc", None)
        if comparable_current != comparable_manifest:
            print("MANIFEST_ERROR ARTIFACT_MANIFEST.json is stale; run make manifest")
            return 1
        print("MANIFEST_PASS")
        return 0
    write_outputs(manifest)
    print("MANIFEST_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
