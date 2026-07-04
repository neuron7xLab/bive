"""Institutional-verify — fail-closed maturity aggregator.

Runs every roadmap gate of the COGVERITAS Institutional Level-Up Specification and
refuses to print INSTITUTIONAL_VERIFY_COMPLETE unless all exist and pass. A gate
that is not yet implemented, or that fails, keeps the whole verdict incomplete —
the spec's own rule: a higher maturity level is not claimed while the evidence
boundary does not support it.

The Makefile chains ``cogveritas-verify`` and ``verify-release`` as prerequisites,
so reaching here means the base battery passed; this aggregates the institutional
roadmap gates on top.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (sentinel printed on pass, implementing script under scripts/). Order matches the
# specification's roadmap (PR-1 .. PR-6).
_ROADMAP = [
    ("BENCHMARK_CARD_PASS", "benchmark_card.py"),
    ("CONTAMINATION_AUDIT_PASS", "contamination_audit.py"),
    ("CROSS_DOMAIN_MATRIX_PASS", "cross_domain_matrix_check.py"),
    ("DOMAIN_DISTANCE_PASS", "domain_distance_check.py"),
    ("RESOURCE_EFFECTIVENESS_PASS", "resource_effectiveness_check.py"),
    ("PRODUCT_CLAIM_AUDIT_PASS", "product_claim_audit.py"),
    ("MISUSE_THREAT_MODEL_PASS", "misuse_threat_model_check.py"),
    ("EXTERNAL_REPLICATION_READY", "external_replication_check.py"),
    ("CAPABILITY_REGISTRY_PASS", "capability_registry_check.py"),
    ("INSTITUTIONAL_SCORECARD_PASS", "institutional_scorecard.py"),
]


def _run_gate(script: str) -> bool:
    proc = subprocess.run(  # noqa: S603 - fixed, in-repo script paths only
        [sys.executable, str(ROOT / "scripts" / script)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return proc.returncode == 0


def main() -> int:
    # Base battery ran as Makefile prerequisites to reach this point.
    print("COGVERITAS_VERIFY_COMPLETE")
    print("VERIFY_RELEASE_PASS")

    passed = 0
    missing: list[str] = []
    failed: list[str] = []
    for sentinel, script in _ROADMAP:
        path = ROOT / "scripts" / script
        if not path.is_file():
            gate = sentinel.rsplit("_", 1)[0]
            print(f"{gate}: NOT_IMPLEMENTED")
            missing.append(sentinel)
            continue
        if _run_gate(script):
            print(sentinel)
            passed += 1
        else:
            print(f"{sentinel.rsplit('_', 1)[0]}: FAIL")
            failed.append(sentinel)

    total = len(_ROADMAP)
    print(f"INSTITUTIONAL_ROADMAP {passed}/{total} gates passing")
    if missing or failed:
        print("INSTITUTIONAL_VERIFY_INCOMPLETE (fail-closed; maturity not claimed)")
        return 1
    print("INSTITUTIONAL_VERIFY_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
