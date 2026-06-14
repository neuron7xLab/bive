from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "verification" / "AUTOMATION_CONTRACT.json"

REQUIRED_MAKE_TARGETS = {
    "verify-release",
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
# Fragments that must appear in the general CI workflow (ci.yml).
REQUIRED_CI_FRAGMENTS = {
    "make verify-release",
    "make dependency-audit",
    "make license-audit",
    "actions/dependency-review-action",
}
# Fragments that must appear in the dedicated, trusted Scorecard workflow.
REQUIRED_SCORECARD_FRAGMENTS = {
    "ossf/scorecard-action",
    "publish_results: true",
}
# The Scorecard publish endpoint (api.securityscorecards.dev) rejects any trusted
# workflow that declares a top-level `env:` or `defaults:` block — that is exactly
# what broke publishing while Scorecard lived inside ci.yml. Encode the contract as
# a hard release gate so a regression fails here, locally, instead of at publish time.
FORBIDDEN_SCORECARD_TOP_LEVEL = {"env", "defaults"}
REQUIRED_SCORECARD_TOP_LEVEL = {"permissions"}


def _top_level_keys(workflow: str) -> set[str]:
    """Mapping keys declared at column 0 — i.e. the workflow's top-level blocks."""
    keys: set[str] = set()
    for line in workflow.splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if match:
            keys.add(match.group(1))
    return keys


def _target_names(makefile: str) -> set[str]:
    names: set[str] = set()
    for line in makefile.splitlines():
        if line.startswith("\t") or not line or line.startswith(".") or ":" not in line:
            continue
        left = line.split(":", 1)[0]
        for token in left.split():
            if re.match(r"^[A-Za-z0-9_.-]+$", token):
                names.add(token)
    return names


def main() -> int:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    verify_script = (ROOT / "scripts" / "verify_release.py").read_text(encoding="utf-8")
    ci_workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    scorecard_path = ROOT / ".github" / "workflows" / "scorecard.yml"
    errors: list[str] = []

    targets = _target_names(makefile)
    missing_targets = sorted(REQUIRED_MAKE_TARGETS - targets)
    if missing_targets:
        errors.append(f"Makefile missing targets: {missing_targets}")

    for gate in sorted(REQUIRED_VERIFY_GATES):
        if f'"{gate}"' not in verify_script:
            errors.append(f"verify_release.py missing gate {gate}")

    for fragment in sorted(REQUIRED_CI_FRAGMENTS):
        if fragment not in ci_workflow:
            errors.append(f"ci.yml missing fragment {fragment}")

    # Scorecard must NOT live in the general CI workflow: ci.yml carries a top-level
    # `env:` that the publish endpoint forbids in a trusted workflow.
    if "ossf/scorecard-action" in ci_workflow:
        errors.append("ci.yml must not run ossf/scorecard-action (trusted-workflow env conflict)")

    # Dedicated, trusted Scorecard workflow.
    if not scorecard_path.exists():
        errors.append("missing .github/workflows/scorecard.yml")
    else:
        scorecard = scorecard_path.read_text(encoding="utf-8")
        for fragment in sorted(REQUIRED_SCORECARD_FRAGMENTS):
            if fragment not in scorecard:
                errors.append(f"scorecard.yml missing fragment {fragment}")
        top_level = _top_level_keys(scorecard)
        for forbidden in sorted(FORBIDDEN_SCORECARD_TOP_LEVEL & top_level):
            errors.append(f"scorecard.yml has forbidden top-level '{forbidden}:' (breaks Scorecard publish)")
        for required in sorted(REQUIRED_SCORECARD_TOP_LEVEL - top_level):
            errors.append(f"scorecard.yml missing required top-level '{required}:'")

    if errors:
        raise SystemExit("AUTOMATION_CONTRACT_FAIL\n" + "\n".join(f"- {e}" for e in errors))

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {
                "status": "pass",
                "make_targets": sorted(targets),
                "release_gates": sorted(REQUIRED_VERIFY_GATES),
                "ci_fragments": sorted(REQUIRED_CI_FRAGMENTS),
                "scorecard_fragments": sorted(REQUIRED_SCORECARD_FRAGMENTS),
                "scorecard_forbidden_top_level": sorted(FORBIDDEN_SCORECARD_TOP_LEVEL),
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
