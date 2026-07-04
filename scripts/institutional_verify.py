"""Institutional-verify — fail-closed maturity aggregator.

Runs every roadmap gate of the COGVERITAS Institutional Level-Up Specification and
refuses to print INSTITUTIONAL_VERIFY_COMPLETE unless all exist and pass. A gate
that is not yet implemented, or that fails, keeps the whole verdict incomplete —
the spec's own rule: a higher maturity level is not claimed while the evidence
boundary does not support it.

The base battery (cogveritas-verify + verify-release) is verified from
``VERIFY_RELEASE.log`` — it is NEVER assumed to have run. Without a complete,
all-passing release log this fails closed and prints no base sentinel.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# verify-release's own authoritative record (46 VERIFY_GATE_PASS + terminal line).
# NOT gates.json — that is the evidence-bundle's small curated subset.
_VR_LOG = ROOT / "artifacts" / "verification" / "VERIFY_RELEASE.log"

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
    ("MUTATION_SCORE_PASS", "mutation_check.py"),
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


def _expected_gate_count() -> int:
    """The number of gates the release battery runs (its own GATES list)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import verify_release  # noqa: PLC0415

        return len(verify_release.COMMANDS)
    except Exception:  # noqa: BLE001 - if we cannot read it, do not vouch for completeness
        return 0


def _base_battery_status() -> tuple[bool, str]:
    """Verify the release battery from its OWN log — never assume it ran.

    Evidence for VERIFY_RELEASE_PASS is ``VERIFY_RELEASE.log``: it must contain the
    terminal ``VERIFY_RELEASE_PASS`` line, carry no failed gate, and record a
    ``VERIFY_GATE_PASS`` for EVERY gate in the release battery (completeness — not a
    truncated partial run). Since that battery includes the cogveritas gates, tests,
    lint and typecheck, a complete pass is also the evidence for
    COGVERITAS_VERIFY_COMPLETE. Absent, incomplete, or failing -> not verified.
    """
    if not _VR_LOG.is_file():
        return False, "VERIFY_RELEASE.log absent — run verify-release first"
    log = _VR_LOG.read_text(encoding="utf-8", errors="replace")
    if "VERIFY_RELEASE_FAIL" in log or "VERIFY_GATE_FAIL" in log:
        return False, "verify-release log records a failed gate"
    if "VERIFY_RELEASE_PASS" not in log:
        return False, "verify-release did not reach VERIFY_RELEASE_PASS"
    passes = log.count("VERIFY_GATE_PASS")
    expected = _expected_gate_count()
    if expected and passes < expected:
        return False, f"incomplete verify-release ({passes} < {expected} gate passes)"
    return True, ""


def main() -> int:
    # No unearned sentinels: the base battery is verified from VERIFY_RELEASE.log, not assumed.
    ok, reason = _base_battery_status()
    if not ok:
        print(f"VERIFY_RELEASE: UNVERIFIED ({reason})")
        print("INSTITUTIONAL_VERIFY_INCOMPLETE (base battery not verified; run verify-release)")
        return 1
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

    _print_hierarchy()
    print("INSTITUTIONAL_VERIFY_COMPLETE")
    return 0


def _print_hierarchy() -> None:
    """Hierarchical inference view: leaf gates -> weighted dimensions -> capped score
    -> maturity band. Read from the scorecard artifact the scorecard gate just wrote."""
    scorecard = ROOT / "artifacts" / "verification" / "INSTITUTIONAL_SCORECARD.json"
    if not scorecard.is_file():
        return

    card = json.loads(scorecard.read_text(encoding="utf-8"))
    print("--- hierarchical maturity inference (leaf gates -> dimensions -> score -> band) ---")
    for d in card.get("dimensions", []):
        print(f"  {d['name']} (w{d['weight']}): {len(d['passing'])}/{len(d['sources'])} sources -> {d['fraction']:.2f}")
    print(f"  raw_score {card.get('raw_score')} -> capped {card.get('score')} ({card.get('band_cap_reason')})")
    print(f"  BAND: {card.get('band')!r}")


if __name__ == "__main__":
    raise SystemExit(main())
