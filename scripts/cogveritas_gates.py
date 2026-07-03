"""COGVERITAS fail-closed release gates.

Each gate reads a committed artifact and fails closed on missing data or a
violated invariant. `verify` runs the full battery and prints the exact terminal
contract. Usage:

    python scripts/cogveritas_gates.py <gate>
    python scripts/cogveritas_gates.py verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bive.cogveritas.output_contract import (  # noqa: E402
    ECE_THRESHOLD,
    COGVERITASOutput,
    contains_forbidden_judgment,
)

V = ROOT / "artifacts" / "verification"
DS = ROOT / "artifacts" / "datasets"
KILL_AUC = 0.60

REQUIRED_ARTIFACTS = [
    V / "PHASE0_VERIFIABILITY.json",
    V / "PHASE0_RELIABILITY_DIAGRAM.json",
    V / "PHASE0_BIAS_BASELINE.json",
    DS / "op_spam_manifest.json",
    DS / "mu3d_manifest.json",
]


class GateFail(Exception):
    pass


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _load(path: Path) -> dict:
    if not path.exists():
        raise GateFail(f"missing artifact: {_rel(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def gate_phase0_verifiability() -> str:
    _load(V / "PHASE0_VERIFIABILITY.json")
    return "PHASE0_VERIFIABILITY_ARTIFACT_PRESENT"


def gate_phase0_metrics() -> str:
    d = _load(V / "PHASE0_VERIFIABILITY.json")
    for b in d["datasets"]:
        if b.get("status") == "computed":
            for k in ("auc", "auc_ci", "ece_before", "ece_after", "brier_before", "brier_after"):
                if b.get(k) is None:
                    raise GateFail(f"{b['name']} missing metric {k}")
    _load(V / "PHASE0_RELIABILITY_DIAGRAM.json")
    return "PHASE0_METRICS_PRESENT"


def gate_subject_independent_auc() -> str:
    d = _load(V / "PHASE0_VERIFIABILITY.json")
    computed = [b for b in d["datasets"] if b.get("status") == "computed"]
    unlocked = bool(d.get("phase1_unlocked"))
    below = [b for b in computed if (b.get("auc") or 0.0) <= KILL_AUC]
    if unlocked and below:
        raise GateFail(f"AUC <= {KILL_AUC} but Phase 1 unlocked: {[b['name'] for b in below]}")
    return "SUBJECT_INDEPENDENT_AUC_GATE_PASS_OR_PHASE1_BLOCKED"


def gate_calibration_ece() -> str:
    d = _load(V / "PHASE0_VERIFIABILITY.json")
    floats_allowed = bool(d.get("float_probability_allowed"))
    bad = [b for b in d["datasets"] if b.get("status") == "computed" and (b.get("ece_after") or 1.0) >= ECE_THRESHOLD]
    if floats_allowed and bad:
        raise GateFail(f"ECE >= {ECE_THRESHOLD} but float probabilities emitted: {[b['name'] for b in bad]}")
    return "CALIBRATION_ECE_GATE_PASS_OR_FLOATS_DISABLED"


def gate_bias_baseline() -> str:
    d = _load(V / "PHASE0_BIAS_BASELINE.json")
    ge = d.get("baseline_greater_or_equal")
    blocked = bool(d.get("release_blocked"))
    if ge and not blocked:
        raise GateFail("bias baseline >= model AUC but release not blocked")
    return "BIAS_BASELINE_GATE_PASS_OR_RELEASE_BLOCKED"


def gate_no_verdict() -> str:
    # 1) The output contract structurally forbids a verdict.
    if COGVERITASOutput.model_fields["verdict"].default is not None:
        raise GateFail("output contract verdict default is not None")
    # 2) Emitted artifacts carry no person-level judgment strings.
    for path in (V / "PHASE0_VERIFIABILITY.json", V / "PHASE0_BIAS_BASELINE.json"):
        hits = contains_forbidden_judgment(path.read_text(encoding="utf-8"))
        if hits:
            raise GateFail(f"forbidden judgment strings in {path.name}: {hits}")
    # 3) The verifiability artifact asserts the invariant and disables floats.
    d = _load(V / "PHASE0_VERIFIABILITY.json")
    if not d.get("no_verdict_invariant_passed"):
        raise GateFail("no_verdict_invariant_passed is false")
    if d.get("float_probability_allowed"):
        raise GateFail("float_probability_allowed must be false in Phase 0")
    return "NO_VERDICT_INVARIANT_PASS"


def gate_artifact_manifest() -> str:
    missing = [_rel(p) for p in REQUIRED_ARTIFACTS if not p.exists()]
    if missing:
        raise GateFail(f"missing required artifacts: {missing}")
    return "ARTIFACT_MANIFEST_PASS"


GATES = {
    "phase0-verifiability": gate_phase0_verifiability,
    "phase0-metrics": gate_phase0_metrics,
    "subject-auc": gate_subject_independent_auc,
    "calibration-ece": gate_calibration_ece,
    "bias-baseline": gate_bias_baseline,
    "no-verdict": gate_no_verdict,
    "artifact-manifest": gate_artifact_manifest,
}


def _run(cmd: list[str]) -> bool:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True).returncode == 0


def verify() -> int:
    ok = True
    # Standard hygiene gates (reuse the existing toolchain).
    tokens = []
    tokens.append(("UNIT_TESTS_PASS", _run([sys.executable, "-m", "pytest", "-q", "-k", "cogveritas or verifiability or contract"])))
    tokens.append(("RUFF_PASS", _run(["ruff", "check", "src/bive/cogveritas", "scripts/cogveritas_gates.py", "scripts/run_phase0_verifiability.py"])))
    tokens.append(("MYPY_STRICT_PASS", _run([sys.executable, "-m", "mypy"])))
    for token, passed in tokens:
        print(token if passed else f"{token}_FAILED")
        ok = ok and passed
    # COGVERITAS artifact gates in the specified order.
    for name in ("phase0-verifiability", "subject-auc", "calibration-ece", "bias-baseline", "no-verdict", "artifact-manifest"):
        try:
            print(GATES[name]())
        except GateFail as exc:
            print(f"GATE_FAIL {name}: {exc}", file=sys.stderr)
            ok = False
    if ok:
        print("COGVERITAS_VERIFY_COMPLETE")
        print("⊛")
        return 0
    return 1


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if arg == "verify":
        return verify()
    if arg not in GATES:
        print(f"unknown gate: {arg}", file=sys.stderr)
        return 2
    try:
        print(GATES[arg]())
        return 0
    except GateFail as exc:
        print(f"GATE_FAIL {arg}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
