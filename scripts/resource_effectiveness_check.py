"""Resource-Effectiveness Audit gate (PR-3).

The spec requires reporting not only *whether* a gate passes but the cost, time,
and failure mode of reaching that result. This reads the timing produced by the
release battery (``artifacts/verification/gates.json``), writes a resource report,
and enforces a wall-time budget so the verification suite cannot silently bloat.

Emits ``RESOURCE_EFFECTIVENESS_PASS``; exits non-zero if the timing artifact is
missing, over budget, or contains a failed gate.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "artifacts" / "verification" / "gates.json"
OUT = ROOT / "artifacts" / "verification" / "RESOURCE_EFFECTIVENESS.json"

# Budgets: the whole battery and any single gate. Generous but bounded — the point
# is that growth is visible and capped, not silent.
_TOTAL_BUDGET_S = 1800.0
_PER_GATE_BUDGET_S = 600.0


def audit() -> tuple[dict[str, object], list[str]]:
    if not GATES.is_file():
        return {}, [f"missing timing artifact: {GATES.relative_to(ROOT)} (run verify-release first)"]
    data = json.loads(GATES.read_text(encoding="utf-8"))
    gates = data.get("gates", [])
    problems: list[str] = []
    per_gate: list[dict[str, object]] = []
    total = 0.0
    for g in gates:
        cmd = " ".join(g.get("command", [])) if isinstance(g.get("command"), list) else str(g.get("command", ""))
        dur = float(g.get("duration_seconds", 0.0))
        total += dur
        per_gate.append({"command": cmd, "duration_seconds": dur, "result": g.get("result", "")})
        if dur > _PER_GATE_BUDGET_S:
            problems.append(f"gate over per-gate budget ({dur:.1f}s > {_PER_GATE_BUDGET_S}s): {cmd}")
        if g.get("result") not in ("pass", ""):
            excerpt = str(g.get("failure_excerpt", ""))[:120]
            problems.append(f"non-passing gate in timing: {cmd} -> {g.get('result')} {excerpt!r}")
    if total > _TOTAL_BUDGET_S:
        problems.append(f"battery over total budget ({total:.1f}s > {_TOTAL_BUDGET_S}s)")

    slowest = sorted(per_gate, key=lambda x: -float(x["duration_seconds"]))[:5]  # type: ignore[arg-type]
    report: dict[str, object] = {
        "gate_count": len(per_gate),
        "total_seconds": round(total, 3),
        "total_budget_seconds": _TOTAL_BUDGET_S,
        "per_gate_budget_seconds": _PER_GATE_BUDGET_S,
        "slowest": slowest,
        "status": "PASS" if not problems else "FAIL",
    }
    return report, problems


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
