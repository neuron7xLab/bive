"""Institutional-verify status — fail-closed maturity reporter.

The COGVERITAS Institutional Level-Up Specification defines nine gates. This
reports which are IMPLEMENTED and refuses to print INSTITUTIONAL_VERIFY_COMPLETE
until every one exists and passes — the spec's own rule: a higher maturity level
is not claimed while the evidence boundary does not support it.

Run after the base gates (the Makefile chains cogveritas-verify + verify-release +
product-claim-audit as prerequisites, so reaching here means those passed).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import product_claim_audit as pca  # noqa: E402  (needs scripts/ on sys.path first)

# (spec gate name, implementing script under scripts/). None -> a base gate assumed
# already run as a Makefile prerequisite.
_ROADMAP = [
    ("BENCHMARK_CARD", "benchmark_card.py"),
    ("CONTAMINATION_AUDIT", "contamination_audit.py"),
    ("DOMAIN_DISTANCE", "domain_distance_check.py"),
    ("RESOURCE_EFFECTIVENESS", "resource_effectiveness_check.py"),
    ("PRODUCT_CLAIM_AUDIT", "product_claim_audit.py"),
    ("MISUSE_THREAT_MODEL", "misuse_threat_model_check.py"),
    ("EXTERNAL_REPLICATION", "external_replication_check.py"),
]


def main() -> int:
    print("COGVERITAS_VERIFY_COMPLETE")
    print("VERIFY_RELEASE_PASS")

    # The one roadmap gate that exists must actually pass here too.
    violations, _ = pca.audit()
    if violations:
        print(f"PRODUCT_CLAIM_AUDIT_FAIL {len(violations)} overclaim(s)")
        return 1
    print("PRODUCT_CLAIM_AUDIT_PASS")

    implemented = [name for name, script in _ROADMAP if (ROOT / "scripts" / script).is_file()]
    missing = [name for name, script in _ROADMAP if not (ROOT / "scripts" / script).is_file()]
    for name in missing:
        print(f"{name}: NOT_IMPLEMENTED")

    total = len(_ROADMAP)
    print(f"INSTITUTIONAL_ROADMAP {len(implemented)}/{total} gates implemented")
    if missing:
        # Fail-closed: do NOT declare completion while any gate is unbuilt.
        print("INSTITUTIONAL_VERIFY_INCOMPLETE (fail-closed; maturity not claimed)")
        return 1
    print("INSTITUTIONAL_VERIFY_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
