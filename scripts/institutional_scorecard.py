"""Institutional Scorecard gate (PR-7) — maturity computed only from passing gates.

Maturity is not asserted; it is *derived* from executable gates. Each scored
dimension runs its source gates; the weighted result maps to a maturity band. There
is no manual override field and no way to raise the score except by making gates pass.

Honesty cap: the top band ("externally replicated benchmark-grade") requires an
*actual third-party replication*, which this repository cannot self-certify. The
external-replication gate only proves the package is *ready*, so the band is capped
at "institution-grade candidate" until a real external replication is recorded.
This makes false maturity impossible.

Writes ``artifacts/verification/INSTITUTIONAL_SCORECARD.json``; emits
``INSTITUTIONAL_SCORECARD_PASS`` when the score is validly computed from gates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "verification" / "INSTITUTIONAL_SCORECARD.json"
GATES = ROOT / "artifacts" / "verification" / "gates.json"

# Weighted dimensions (name, weight, sources); weights sum to 100. Sources are gate
# scripts or named proxies.
_DIMENSIONS: list[tuple[str, int, list[str]]] = [
    ("architecture_discipline", 10, ["capability_registry_check.py", "validate_dependency_contracts.py"]),
    ("risk_governance", 15, ["misuse_threat_model_check.py", "proxy:release_governance"]),
    ("metric_validity", 15, ["benchmark_card.py", "contamination_audit.py"]),
    ("cross_domain_evidence", 10, ["cross_domain_matrix_check.py", "domain_distance_check.py"]),
    ("ci_release_discipline", 10, ["proxy:ci_release_status"]),
    ("data_reproducibility", 15, ["external_replication_check.py"]),
    ("resource_effectiveness", 10, ["resource_effectiveness_check.py"]),
    ("product_claim_control", 15, ["product_claim_audit.py"]),
]

_BANDS = [
    (9.0, "externally replicated benchmark-grade system"),
    (8.0, "institution-grade candidate"),
    (7.0, "credible product-research system"),
    (6.0, "strong internal research prototype"),
    (0.0, "prototype"),
]
# Without a recorded third-party replication, the band cannot exceed this.
_UNREPLICATED_CAP = 8.9


def _proxy(name: str) -> bool:
    if name == "ci_release_status":
        if not GATES.is_file():
            return False
        # ci_release_discipline is earned only by a COMPLETE, all-passing release run
        # — evidenced by VERIFY_RELEASE.log, not the evidence-bundle's 4-gate subset.
        log_path = ROOT / "artifacts" / "verification" / "VERIFY_RELEASE.log"
        if not log_path.is_file():
            return False
        log = log_path.read_text(encoding="utf-8", errors="replace")
        if "VERIFY_RELEASE_FAIL" in log or "VERIFY_GATE_FAIL" in log:
            return False
        if "VERIFY_RELEASE_PASS" not in log:
            return False
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import verify_release  # noqa: PLC0415

            expected = len(verify_release.COMMANDS)
        except Exception:  # noqa: BLE001
            expected = 0
        return not (expected and log.count("VERIFY_GATE_PASS") < expected)
    if name == "release_governance":
        # File existence proves NO governance ran — verify_release.py and SECURITY.md
        # sitting in the repo is a checkbox that can never fail. Earn this dimension
        # from evidence that the recorded release battery actually EXECUTED and PASSED
        # the governance gates.
        if not ((ROOT / "scripts" / "verify_release.py").is_file() and (ROOT / "SECURITY.md").is_file()):
            return False
        log_path = ROOT / "artifacts" / "verification" / "VERIFY_RELEASE.log"
        if not log_path.is_file():
            return False
        log = log_path.read_text(encoding="utf-8", errors="replace")
        if "VERIFY_RELEASE_FAIL" in log or "VERIFY_GATE_FAIL" in log or "VERIFY_RELEASE_PASS" not in log:
            return False
        # Named governance gates must each show a recorded pass — not merely a complete
        # run (that is ci_release_status). This asserts the risk-governance gates ran.
        governance_gates = ("threat-model", "security-static", "misuse-threat-model", "product-claim-audit")
        return all(f"VERIFY_GATE_PASS {gate}" in log for gate in governance_gates)
    return False


def _passes(source: str) -> bool:
    if source.startswith("proxy:"):
        return _proxy(source.split(":", 1)[1])
    script = ROOT / "scripts" / source
    if not script.is_file():
        return False
    proc = subprocess.run(  # noqa: S603 - fixed in-repo script paths
        [sys.executable, str(script)], capture_output=True, text=True, cwd=ROOT
    )
    return proc.returncode == 0


def _band(score: float) -> str:
    for threshold, label in _BANDS:
        if score >= threshold:
            return label
    return "prototype"


def compute() -> dict[str, object]:
    dims: list[dict[str, object]] = []
    weighted = 0.0
    for name, weight, sources in _DIMENSIONS:
        passing = [s for s in sources if _passes(s)]
        frac = len(passing) / len(sources) if sources else 0.0
        weighted += weight * frac
        dims.append(
            {"name": name, "weight": weight, "sources": sources, "passing": passing, "fraction": round(frac, 3)}
        )
    raw_score = round(weighted / 10.0, 2)  # 0-100 -> 0-10

    externally_replicated = False  # no third-party replication recorded
    capped_score = min(raw_score, _UNREPLICATED_CAP) if not externally_replicated else raw_score
    return {
        "dimensions": dims,
        "raw_score": raw_score,
        "externally_replicated": externally_replicated,
        "band_cap_reason": "no third-party replication recorded; capped below benchmark-grade",
        "score": capped_score,
        "band": _band(capped_score),
        "computed_from_gates": True,
        "manual_override": False,
    }


def _integrity_problems(card: dict[str, object]) -> list[str]:
    """Verify the card is a well-formed, gate-derived computation.

    ``computed_from_gates``/``manual_override`` are literal constants in ``compute``
    and can never flip, so asserting them proves nothing. This instead re-derives the
    scoring math from the recorded dimensions and fails on any inconsistency — the
    honest pass condition is that the computation is internally sound, not that the
    score is high.
    """
    problems: list[str] = []
    if card.get("manual_override") or not card.get("computed_from_gates"):
        problems.append("computation not gate-derived")

    dims = card.get("dimensions")
    if not isinstance(dims, list) or not dims:
        problems.append("scorecard has no dimensions")
        return problems

    known_sources = {s for _n, _w, srcs in _DIMENSIONS for s in srcs}
    total_weight = 0
    weighted = 0.0
    for d in dims:
        name = d.get("name")
        weight = d.get("weight")
        sources = d.get("sources", [])
        passing = d.get("passing", [])
        frac = d.get("fraction")
        if not isinstance(weight, int) or not isinstance(sources, list) or not sources:
            problems.append(f"{name}: malformed dimension")
            continue
        total_weight += weight
        if not set(passing).issubset(set(sources)):
            problems.append(f"{name}: passing not a subset of sources")
        if not set(sources).issubset(known_sources):
            problems.append(f"{name}: cites an unknown gate source")
        expected_frac = round(len(passing) / len(sources), 3)
        if frac != expected_frac:
            problems.append(f"{name}: fraction {frac} != {expected_frac} (len passing/sources)")
        weighted += weight * (frac if isinstance(frac, (int, float)) else -1.0)

    if total_weight != 100:
        problems.append(f"dimension weights sum to {total_weight}, not 100")

    raw = card.get("raw_score")
    if raw != round(weighted / 10.0, 2):
        problems.append(f"raw_score {raw} does not match re-derived {round(weighted / 10.0, 2)}")

    score = card.get("score")
    replicated = bool(card.get("externally_replicated"))
    if isinstance(score, (int, float)) and isinstance(raw, (int, float)):
        if score > raw:
            problems.append(f"capped score {score} exceeds raw {raw}")
        if not replicated and score > _UNREPLICATED_CAP:
            problems.append(f"score {score} exceeds unreplicated cap {_UNREPLICATED_CAP}")
        if card.get("band") != _band(float(score)):
            problems.append(f"band {card.get('band')!r} does not match score {score}")
    else:
        problems.append("score/raw_score not numeric")
    return problems


def main() -> int:
    card = compute()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(card, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Integrity of the computation is the pass condition — not a high score.
    problems = _integrity_problems(card)
    if problems:
        for p in problems:
            print(f"INSTITUTIONAL_SCORECARD_ISSUE {p}")
        print(f"INSTITUTIONAL_SCORECARD_FAIL {len(problems)} integrity issue(s)")
        return 1
    print(f"INSTITUTIONAL_SCORECARD_PASS score={card['score']} band={card['band']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
