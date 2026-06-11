from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "verification" / "AUTOMATION_CONTRACT.json"

REQUIRED_MAKE_TARGETS = {
    "verify-release",
    "verify-bootstrap",
    "env-check",
    "check-dependencies",
    "check-repo-clean",
    "test",
    "coverage",
    "lint",
    "typecheck",
    "schema",
    "dependency-contracts",
    "test-architecture",
    "automation-contract",
    "bibliography",
    "threat-model",
    "microsoft-rest",
    "operational-excellence",
    "aos-kernel",
    "cognitive-control",
    "frontend-quality",
    "science-registry",
    "dynamic-probe",
    "security-static",
    "dependency-audit",
    "license-audit",
    "openapi",
    "manifest-check",
    "wheel-smoke",
    "repo-clean",
    "evidence-bundle",
}
REQUIRED_VERIFY_GATES = {
    "repo-clean",
    "metadata",
    "dependency-contracts",
    "test-architecture",
    "automation-contract",
    "bibliography",
    "threat-model",
    "microsoft-rest",
    "operational-excellence",
    "aos-kernel",
    "cognitive-control",
    "lint",
    "typecheck",
    "coverage",
    "schema",
    "api-smoke",
    "frontend-quality",
    "science-registry",
    "dynamic-probe",
    "openapi",
    "security-static",
    "wheel-smoke",
    "manifest-check",
}
REQUIRED_WORKFLOW_FRAGMENTS = {
    "make verify-release",
    "make dependency-audit",
    "make license-audit",
    "actions/dependency-review-action",
    "ossf/scorecard-action",
}


def _target_names(makefile: str) -> set[str]:
    names: set[str] = set()
    for line in makefile.splitlines():
        if line.startswith("\t") or not line or line.startswith(".") or ":" not in line or ":=" in line:
            continue
        left = line.split(":", 1)[0]
        if "=" in left:
            continue
        for token in left.split():
            if re.match(r"^[A-Za-z0-9_.-]+$", token):
                names.add(token)
    return names


def main() -> int:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    verify_script = (ROOT / "scripts" / "verify_release.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    errors: list[str] = []

    targets = _target_names(makefile)
    missing_targets = sorted(REQUIRED_MAKE_TARGETS - targets)
    if missing_targets:
        errors.append(f"Makefile missing targets: {missing_targets}")

    for gate in sorted(REQUIRED_VERIFY_GATES):
        if f'"{gate}"' not in verify_script:
            errors.append(f"verify_release.py missing gate {gate}")

    for fragment in sorted(REQUIRED_WORKFLOW_FRAGMENTS):
        if fragment not in workflow:
            errors.append(f"ci.yml missing fragment {fragment}")

    if errors:
        raise SystemExit("AUTOMATION_CONTRACT_FAIL\n" + "\n".join(f"- {e}" for e in errors))

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {
                "status": "pass",
                "make_targets": sorted(targets),
                "release_gates": sorted(REQUIRED_VERIFY_GATES),
                "workflow_fragments": sorted(REQUIRED_WORKFLOW_FRAGMENTS),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("AUTOMATION_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
