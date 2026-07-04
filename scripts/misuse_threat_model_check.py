"""Misuse and Human-Impact Threat Model gate (PR-5).

Validates that the threat model exists, covers the required misuse scenarios, and
that every safeguard it names maps to a mechanism that actually exists in the
repository — a safeguard is not credible if the file it cites is absent.

Emits ``MISUSE_THREAT_MODEL_PASS``; exits non-zero on a missing scenario or a
safeguard whose mechanism cannot be found.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "methodology" / "MISUSE_THREAT_MODEL.md"

# Misuse scenarios the model MUST address (by marker in the doc).
_REQUIRED_SCENARIOS = (
    "guilt-by-gap",
    "coercive interviewing",
    "lie-detector overclaim",
    "out-of-domain application",
    "surveillance overreach",
    "evidence tampering",
)

# Safeguard -> the mechanism file that must exist for the safeguard to be real.
_MECHANISMS = {
    "no-verdict invariant": "src/bive/cogveritas/output_contract.py",
    "interview.py": "src/bive/cogveritas/interview.py",
    "product_claim_audit.py": "scripts/product_claim_audit.py",
    "domain_distance_check.py": "scripts/domain_distance_check.py",
    "integrity.py": "src/bive/cogveritas/integrity.py",
    "capabilities.py": "src/bive/cogveritas/capabilities.py",
}


def check() -> list[str]:
    if not DOC.is_file():
        return [f"missing threat model: {DOC.relative_to(ROOT)}"]
    problems: list[str] = []
    text = DOC.read_text(encoding="utf-8")
    lowered = text.lower()
    for scenario in _REQUIRED_SCENARIOS:
        if scenario not in lowered:
            problems.append(f"threat model omits required scenario: {scenario!r}")
    if "safeguard" not in lowered:
        problems.append("threat model names no safeguards")
    # Every cited mechanism must exist (a safeguard that points nowhere is theatre).
    for label, rel in _MECHANISMS.items():
        if label in text and not (ROOT / rel).is_file():
            problems.append(f"safeguard cites a missing mechanism: {label} -> {rel}")
    # At least the core invariant safeguard must be present and real.
    if "verdict` is structurally `null" not in text and "verdict is structurally null" not in lowered:
        problems.append("threat model does not assert the structural no-verdict safeguard")
    return problems


def main() -> int:
    problems = check()
    if problems:
        for p in problems:
            print(f"MISUSE_THREAT_MODEL_ISSUE {p}")
        print(f"MISUSE_THREAT_MODEL_FAIL {len(problems)} issue(s)")
        return 1
    print("MISUSE_THREAT_MODEL_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
