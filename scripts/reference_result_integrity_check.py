"""Frozen reference-result integrity, falsification and provenance gate.

The public benchmark card (docs/methodology/BENCHMARK_CARD.md) is bound to a frozen
empirical result, ``research/cogveritas/phase0_results.json``. That frozen file is the
pre-registration of BIVE's one anchored capability claim (verbal-science verifiability
features separate deceptive from truthful text on the real Ott corpus). Until now
nothing pinned its bytes, recorded its evidence tier, or re-derived its falsifiable
invariants — the numbers were trusted by assertion.

This gate makes the anchored claim self-auditing and fail-closed. It:

  * pins the frozen result's sha256 to a reviewed provenance sidecar (a result change
    without a matching pin update is rejected — pre-registration, not drift);
  * requires an explicit ANCHORED evidence tier with a complete, real provenance
    record (data source, license, protocol, seed, code entrypoint, metric defs);
  * RE-DERIVES the kill-gate verdict from the numbers instead of trusting the stored
    one (kills the tautology of a self-declared PASS);
  * enforces the falsifiable structure of the experiment — the baseline must be a
    genuine null control (its 95% CI brackets chance), the headline must be
    statistically separated from both chance and the baseline (non-overlapping CI),
    and the leakage ceiling must be declared contaminated, not read as capability.

Any violation exits non-zero. Emits REFERENCE_RESULT_INTEGRITY.json.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "research" / "cogveritas" / "phase0_results.json"
PROVENANCE = ROOT / "research" / "cogveritas" / "phase0_provenance.json"
OUT = ROOT / "artifacts" / "verification" / "REFERENCE_RESULT_INTEGRITY.json"

CHANCE = 0.5
# An ANCHORED headline that also claims honest calibration must actually be calibrated.
_ECE_MAX = 0.10
_REQUIRED_PROVENANCE = ("evidence_tier", "claim", "frozen_reference", "data_source", "protocol", "kill_gate", "model_roles")
_REQUIRED_DATA_SOURCE = ("name", "canonical_url", "loader_entrypoint", "license_notes", "label_schema")
_REQUIRED_PROTOCOL = ("description", "seed", "cv_folds", "code_ref", "metric_definitions")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _ci(row: dict[str, Any]) -> tuple[float, float] | None:
    ci = row.get("auc_ci95")
    if isinstance(ci, list) and len(ci) == 2 and all(isinstance(x, (int, float)) for x in ci):
        return float(ci[0]), float(ci[1])
    return None


def check(results_data: dict[str, Any], provenance: dict[str, Any], actual_sha: str) -> list[str]:
    """Return a list of integrity violations; empty means the anchored claim holds.

    Pure over its inputs so tests can mutate a copy and prove each invariant CAN fail.
    """
    problems: list[str] = []

    # INV-1: byte-freeze — the frozen result must match the reviewed pin.
    pinned = (provenance.get("frozen_reference") or {}).get("sha256")
    if pinned != actual_sha:
        problems.append(f"frozen result sha256 {actual_sha} != pinned {pinned} (pre-registration drift)")

    # INV-2: complete ANCHORED provenance.
    if provenance.get("evidence_tier") != "ANCHORED":
        problems.append(f"evidence_tier must be ANCHORED, got {provenance.get('evidence_tier')!r}")
    for key in _REQUIRED_PROVENANCE:
        if key not in provenance:
            problems.append(f"provenance missing required block: {key}")
    for key in _REQUIRED_DATA_SOURCE:
        if key not in (provenance.get("data_source") or {}):
            problems.append(f"data_source missing: {key}")
    for key in _REQUIRED_PROTOCOL:
        if key not in (provenance.get("protocol") or {}):
            problems.append(f"protocol missing: {key}")

    rows = {r.get("model", ""): r for r in results_data.get("results", [])}
    roles = provenance.get("model_roles") or {}

    # INV-3: declared roles must resolve to real rows in the frozen result.
    resolved: dict[str, dict[str, Any]] = {}
    for role in ("headline", "baseline", "ceiling"):
        name = (roles.get(role) or {}).get("model")
        if name not in rows:
            problems.append(f"model_roles.{role} '{name}' not found in frozen results")
        else:
            resolved[role] = rows[name]
    if len(resolved) < 3:
        return problems  # cannot evaluate structure without all three roles

    head, base, ceil = resolved["headline"], resolved["baseline"], resolved["ceiling"]
    head_auc, ceil_auc = _num(head.get("roc_auc")), _num(ceil.get("roc_auc"))
    head_ci, base_ci = _ci(head), _ci(base)

    # INV-4: baseline is a genuine null control — its 95% CI brackets chance.
    if base_ci is None:
        problems.append("baseline has no auc_ci95 — cannot prove it is a null control")
    elif not (base_ci[0] <= CHANCE <= base_ci[1]):
        problems.append(f"baseline CI {base_ci} does not bracket chance {CHANCE} — not a valid null control")

    # INV-5: headline is statistically separated from chance AND from the baseline.
    if head_ci is None:
        problems.append("headline has no auc_ci95 — cannot prove separation from chance")
    else:
        if head_ci[0] <= CHANCE:
            problems.append(f"headline CI lower bound {head_ci[0]} not above chance {CHANCE}")
        if base_ci is not None and head_ci[0] <= base_ci[1]:
            problems.append(f"headline CI {head_ci} overlaps baseline CI {base_ci} — lift unproven")

    # INV-6: re-derive the kill-gate verdict instead of trusting the stored one.
    threshold = _num((provenance.get("kill_gate") or {}).get("threshold_auc"))
    frozen_kill = results_data.get("kill_gate") or {}
    frozen_threshold = _num(frozen_kill.get("threshold_auc"))
    if threshold is None:
        problems.append("provenance kill_gate.threshold_auc missing/non-numeric")
    elif frozen_threshold != threshold:
        problems.append(f"frozen threshold {frozen_threshold} != provenance threshold {threshold}")
    if threshold is not None and head_auc is not None:
        derived = "PASS" if head_auc >= threshold else "FAIL"
        stored = frozen_kill.get("verdict")
        if stored != derived:
            problems.append(f"kill_gate verdict {stored!r} != re-derived {derived!r} (auc {head_auc} vs thr {threshold})")
        if derived != "PASS":
            problems.append(f"headline auc {head_auc} below kill threshold {threshold} — anchored claim falsified")

    # INV-7: the ceiling must be an above-headline leak, declared contaminated.
    if head_auc is not None and ceil_auc is not None and ceil_auc <= head_auc:
        problems.append(f"ceiling auc {ceil_auc} not above headline {head_auc} — not a ceiling")
    if (roles.get("ceiling") or {}).get("contaminated") is not True:
        problems.append("model_roles.ceiling.contaminated must be true — a high-AUC leak read as capability is dishonest")

    # INV-8: an anchored claim of honest calibration must actually be calibrated.
    head_ece = _num(head.get("ece"))
    if head_ece is None:
        problems.append("headline has no ece — calibration claim unbacked")
    elif head_ece > _ECE_MAX:
        problems.append(f"headline ece {head_ece} exceeds calibration ceiling {_ECE_MAX}")

    return problems


def main() -> int:
    if not FROZEN.is_file():
        print(f"REFERENCE_RESULT_INTEGRITY_FAIL frozen result absent: {FROZEN}")
        return 1
    if not PROVENANCE.is_file():
        print(f"REFERENCE_RESULT_INTEGRITY_FAIL provenance sidecar absent: {PROVENANCE}")
        return 1

    results_data = json.loads(FROZEN.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    actual_sha = _sha256(FROZEN)
    problems = check(results_data, provenance, actual_sha)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "pass" if not problems else "fail",
                "evidence_tier": provenance.get("evidence_tier"),
                "frozen_reference": "research/cogveritas/phase0_results.json",
                "checks": [
                    "byte-freeze pin",
                    "complete ANCHORED provenance",
                    "roles resolve to frozen rows",
                    "baseline CI brackets chance",
                    "headline separated from chance and baseline",
                    "kill-gate verdict re-derived",
                    "ceiling declared contaminated",
                    "headline calibrated",
                ],
                "problems": problems,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    if problems:
        for problem in problems:
            print(f"REFERENCE_RESULT_INTEGRITY_ISSUE {problem}")
        print(f"REFERENCE_RESULT_INTEGRITY_FAIL {len(problems)} issue(s)")
        return 1
    print("REFERENCE_RESULT_INTEGRITY_PASS anchored claim self-audited and falsifiable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
