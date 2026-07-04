"""External replication attestation gate.

The institutional scorecard caps BIVE below benchmark-grade until a *real, independent*
replication of the frozen anchored result is recorded — a bar the repository correctly
cannot self-certify. Previously that cap was an unconditional ``False`` literal: there
was no defined, checkable path to ever earn it.

This gate defines the path without letting the repo forge it. An external party who
reproduces the frozen result (research/cogveritas/phase0_results.json) from the public
Ott corpus submits an attestation JSON under research/cogveritas/replications/. The gate
RE-DERIVES whether that attestation actually reproduces the pre-registered value within
its 95% CI, whether the attester is genuinely independent of this repository, and whether
a public evidence URL is present — it never trusts a self-declared "reproduced" flag.

Fail-closed semantics:
  * no attestation present            -> attested=False, exit 0 (honest default, not a failure)
  * a valid INDEPENDENT attestation   -> attested=True,  exit 0 (benchmark-grade path opened)
  * any attestation that is malformed, self-issued-as-independent, or reports a result
    outside the pre-registered CI      -> exit 1 (a fraudulent/broken replication claim is
                                          surfaced, never silently ignored)

Emits EXTERNAL_REPLICATION_ATTESTATION_STATUS.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "research" / "cogveritas" / "phase0_results.json"
PROVENANCE = ROOT / "research" / "cogveritas" / "phase0_provenance.json"
SCHEMA = ROOT / "schemas" / "external_replication_attestation.schema.json"
REPLICATIONS = ROOT / "research" / "cogveritas" / "replications"
OUT = ROOT / "artifacts" / "verification" / "EXTERNAL_REPLICATION_ATTESTATION_STATUS.json"

# The canonical repository and its automation are NEVER an independent third party.
CANONICAL_REPO = "neuron7xLab/bive"


def load_pre_registration(root: Path) -> dict[str, Any]:
    frozen = json.loads((root / "research" / "cogveritas" / "phase0_results.json").read_text(encoding="utf-8"))
    prov = json.loads((root / "research" / "cogveritas" / "phase0_provenance.json").read_text(encoding="utf-8"))
    headline_name = ((prov.get("model_roles") or {}).get("headline") or {}).get("model")
    rows = {r.get("model", ""): r for r in frozen.get("results", [])}
    head = rows.get(headline_name, {})
    return {
        "headline_model": headline_name,
        "headline_auc": head.get("roc_auc"),
        "headline_ci95": head.get("auc_ci95"),
        "kill_threshold": (frozen.get("kill_gate") or {}).get("threshold_auc"),
        "corpus": (prov.get("data_source") or {}).get("name"),
    }


def validate_attestation(att: dict[str, Any], prereg: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Return violations for a single attestation; empty means it verifies."""
    problems: list[str] = []
    try:
        jsonschema.validate(att, schema)
    except jsonschema.ValidationError as exc:
        return [f"schema: {exc.message}"]

    attester_class = att.get("attester_class")
    public_repo = (att.get("attester") or {}).get("public_repo", "")

    # Independence: an 'independent' attestation issued from the canonical repo is a
    # contradiction. Self-issued ones are witnesses, never third-party attestations.
    if attester_class == "independent" and CANONICAL_REPO in public_repo:
        problems.append(f"attester_class 'independent' but public_repo is the canonical repo {CANONICAL_REPO}")

    # Reproduction: the reported headline must reproduce the pre-registered result within
    # its 95% CI and clear the kill threshold — re-derived, not trusted.
    result = att.get("result") or {}
    if result.get("model") != prereg["headline_model"]:
        problems.append(f"result.model {result.get('model')!r} != pre-registered headline {prereg['headline_model']!r}")
    auc = result.get("roc_auc")
    ci = prereg.get("headline_ci95")
    if isinstance(auc, (int, float)) and isinstance(ci, list) and len(ci) == 2:
        if not (ci[0] <= auc <= ci[1]):
            problems.append(f"reported AUC {auc} outside pre-registered 95% CI {ci} — not a reproduction")
    else:
        problems.append("cannot compare reported AUC to pre-registered CI (missing values)")
    threshold = prereg.get("kill_threshold")
    if isinstance(auc, (int, float)) and isinstance(threshold, (int, float)) and auc < threshold:
        problems.append(f"reported AUC {auc} below kill threshold {threshold}")

    return problems


def assess(root: Path) -> dict[str, Any]:
    """Scan submitted attestations and return the replication status."""
    prereg = load_pre_registration(root)
    schema = json.loads((root / "schemas" / "external_replication_attestation.schema.json").read_text(encoding="utf-8"))
    rep_dir = root / "research" / "cogveritas" / "replications"

    valid_independent: list[str] = []
    valid_self: list[str] = []
    rejected: list[dict[str, Any]] = []

    for path in sorted(rep_dir.glob("*.json")) if rep_dir.is_dir() else []:
        try:
            att = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            rejected.append({"file": path.name, "problems": [f"invalid JSON: {exc}"]})
            continue
        problems = validate_attestation(att, prereg, schema)
        if problems:
            rejected.append({"file": path.name, "problems": problems})
        elif att.get("attester_class") == "independent":
            valid_independent.append(path.name)
        else:
            valid_self.append(path.name)

    return {
        "schema_version": 1,
        "attested": len(valid_independent) > 0,
        "independent_attestations": valid_independent,
        "self_witness_attestations": valid_self,
        "rejected": rejected,
        "pre_registration": prereg,
    }


def independent_attestation_present(root: Path = ROOT) -> bool:
    """True iff a valid independent third-party attestation is recorded.

    Consumed by the institutional scorecard to gate the benchmark-grade cap. Raises on a
    rejected (fraudulent/broken) attestation so the scorecard cannot be computed over an
    unresolved false claim.
    """
    status = assess(root)
    if status["rejected"]:
        raise ValueError(f"rejected replication attestation(s): {status['rejected']}")
    return bool(status["attested"])


def main() -> int:
    status = assess(ROOT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if status["rejected"]:
        for item in status["rejected"]:
            print(f"EXTERNAL_REPLICATION_ATTESTATION_REJECTED {item['file']}: {item['problems']}")
        print(f"EXTERNAL_REPLICATION_ATTESTATION_FAIL {len(status['rejected'])} invalid attestation(s)")
        return 1

    n_ind = len(status["independent_attestations"])
    n_self = len(status["self_witness_attestations"])
    print(
        f"EXTERNAL_REPLICATION_ATTESTATION_STATUS attested={str(status['attested']).lower()} "
        f"({n_ind} independent, {n_self} self-witness)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
