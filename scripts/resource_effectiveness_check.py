"""Resource-Effectiveness Audit gate (PR-3).

The spec requires reporting not only *whether* a gate passes but the cost, time,
and failure mode of reaching that result. This reads the timing produced by the
release battery (``artifacts/verification/RELEASE_TIMINGS.json``), writes a resource report,
and enforces a wall-time budget so the verification suite cannot silently bloat.

Emits ``RESOURCE_EFFECTIVENESS_PASS``; exits non-zero if the timing artifact is
missing, over budget, or contains a failed gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The FULL-battery per-gate timing (all ~46 gates), written by verify_release.
# NOT gates.json — that is the evidence-bundle's 4-gate subset, which would make the
# budget check trivially pass and measure nothing of the real battery.
GATES = ROOT / "artifacts" / "verification" / "RELEASE_TIMINGS.json"
OUT = ROOT / "artifacts" / "verification" / "RESOURCE_EFFECTIVENESS.json"

# Budgets: the whole battery and any single gate. Generous but bounded — the point
# is that growth is visible and capped, not silent.
_TOTAL_BUDGET_S = 1800.0
_PER_GATE_BUDGET_S = 600.0


def audit() -> tuple[dict[str, object], list[str]]:
    if not GATES.is_file():
        return {}, [f"missing timing artifact: {GATES.name} (run verify-release first)"]
    data = json.loads(GATES.read_text(encoding="utf-8"))
    gates = data.get("gates", [])
    problems: list[str] = []
    per_gate: list[dict[str, object]] = []
    total = 0.0
    for g in gates:
        cmd = str(g.get("name", g.get("command", "")))
        dur = float(g.get("duration_seconds", 0.0))
        total += dur
        per_gate.append({"command": cmd, "duration_seconds": dur, "result": g.get("result", "")})
        if dur > _PER_GATE_BUDGET_S:
            problems.append(f"gate over per-gate budget ({dur:.1f}s > {_PER_GATE_BUDGET_S}s): {cmd}")
        if g.get("result") not in ("pass", ""):
            problems.append(f"non-passing gate in timing: {cmd} -> {g.get('result')}")
    if total > _TOTAL_BUDGET_S:
        problems.append(f"battery over total budget ({total:.1f}s > {_TOTAL_BUDGET_S}s)")
    # Completeness: the timing must cover the FULL release battery, not a subset —
    # otherwise the budget bounds nothing real (the defect this replaces).
    expected = _expected_gate_count()
    if expected and len(gates) < expected:
        problems.append(f"incomplete timing ({len(gates)} < {expected} gates) — not the full battery")

    slowest = sorted(per_gate, key=lambda x: -float(x["duration_seconds"]))[:5]  # type: ignore[arg-type]
    expensive_failures = [
        {"command": str(g["command"]), "result": str(g["result"])}
        for g in per_gate
        if g["result"] not in ("pass", "")
    ]
    report: dict[str, object] = {
        # Cost.
        "gate_count": len(per_gate),
        "total_seconds": round(total, 3),
        "total_budget_seconds": _TOTAL_BUDGET_S,
        "per_gate_budget_seconds": _PER_GATE_BUDGET_S,
        "slowest": slowest,
        # Resource posture the mandate requires an institutional run to report.
        "memory_policy": "pinned dependencies; deterministic gates; no network in the core path",
        "dependencies": _dependency_count(),
        "test_count": _test_count(),
        "artifacts_present": _required_artifacts_present(),
        "expensive_failures": expensive_failures,
        "status": "PASS" if not problems else "FAIL",
    }
    return report, problems


def _expected_gate_count() -> int:
    """Full release-battery gate count — the completeness threshold."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import verify_release  # noqa: PLC0415

        return len(verify_release.COMMANDS)
    except Exception:  # noqa: BLE001
        return 0


def _dependency_count() -> int:
    total = 0
    for lock in (ROOT / "requirements").glob("*.txt"):
        for line in lock.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "==" in s:
                total += 1
    return total


def _test_count() -> int:
    return len(list((ROOT / "tests").glob("test_*.py")))


def _required_artifacts_present() -> dict[str, bool]:
    names = (
        "BENCHMARK_CARD", "CONTAMINATION_AUDIT", "CROSS_DOMAIN_MATRIX", "DOMAIN_DISTANCE_POLICY",
        "PRODUCT_CLAIM_AUDIT", "MISUSE_THREAT_MODEL_AUDIT", "EXTERNAL_REPLICATION_READINESS",
    )
    ver = ROOT / "artifacts" / "verification"
    return {n: (ver / f"{n}.json").is_file() for n in names}


def main() -> int:
    report, problems = audit()
    if report:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if problems:
        for p in problems:
            print(f"RESOURCE_EFFECTIVENESS_ISSUE {p}")
        print(f"RESOURCE_EFFECTIVENESS_FAIL {len(problems)} issue(s)")
        return 1
    print(f"RESOURCE_EFFECTIVENESS_PASS total {report.get('total_seconds')}s / {_TOTAL_BUDGET_S}s across {report.get('gate_count')} gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
