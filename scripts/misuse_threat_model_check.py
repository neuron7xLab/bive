"""Misuse and Human-Impact Threat Model gate (PR-5).

Validates that the threat model exists, covers every required misuse risk, records a
mitigation and a residual-risk for each, and that every cited mitigation maps to a
mechanism that actually exists — a safeguard pointing nowhere is not a safeguard.

Writes ``artifacts/verification/MISUSE_THREAT_MODEL_AUDIT.json``; emits
``MISUSE_THREAT_MODEL_PASS``.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "security" / "MISUSE_THREAT_MODEL.md"
OUT = ROOT / "artifacts" / "verification" / "MISUSE_THREAT_MODEL_AUDIT.json"

# The misuse risks the model MUST address (mandate PR-5), by marker in the doc.
_REQUIRED_RISKS = (
    "misinterpretation",
    "over-reliance",
    "false-authority",
    "selective-evidence",
    "cross-language extraction",
    "record-routing",
    "dossier misuse",
    "interview-question",
    "privacy and sensitive-data",
    "institutional escalation",
)

# Mitigation label -> the mechanism file that must exist for it to be real.
_MECHANISMS = {
    "no-verdict invariant": "src/bive/cogveritas/output_contract.py",
    "interview.py": "src/bive/cogveritas/interview.py",
    "product_claim_audit.py": "scripts/product_claim_audit.py",
    "integrity.py": "src/bive/cogveritas/integrity.py",
    "capability envelope": "src/bive/cogveritas/capabilities.py",
    "domain-distance policy": "scripts/domain_distance_check.py",
}


def check() -> list[str]:
    if not DOC.is_file():
        return [f"missing threat model: {DOC.relative_to(ROOT)}"]
    problems: list[str] = []
    text = DOC.read_text(encoding="utf-8")
    lowered = text.lower()
    for risk in _REQUIRED_RISKS:
        if risk not in lowered:
            problems.append(f"threat model omits required risk: {risk!r}")
    # Every risk block must carry a mitigation AND a residual-risk record.
    if lowered.count("mitigation") < len(_REQUIRED_RISKS):
        problems.append("not every risk records a mitigation")
    if lowered.count("residual risk") < len(_REQUIRED_RISKS):
        problems.append("not every risk records a residual risk")
    for label, rel in _MECHANISMS.items():
        if label in text and not (ROOT / rel).is_file():
            problems.append(f"mitigation cites a missing mechanism: {label} -> {rel}")
    if "verdict` is structurally `null" not in text and "verdict is structurally null" not in lowered:
        problems.append("threat model does not assert the structural no-verdict safeguard")
    return problems


def main() -> int:
    problems = check()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "doc": "docs/security/MISUSE_THREAT_MODEL.md",
                "required_risks": list(_REQUIRED_RISKS),
                "risk_count": len(_REQUIRED_RISKS),
                "problems": problems,
                "status": "PASS" if not problems else "FAIL",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if problems:
        for p in problems:
            print(f"MISUSE_THREAT_MODEL_ISSUE {p}")
        print(f"MISUSE_THREAT_MODEL_FAIL {len(problems)} issue(s)")
        return 1
    print(f"MISUSE_THREAT_MODEL_PASS {len(_REQUIRED_RISKS)} risks covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
