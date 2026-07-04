"""Cross-Domain Matrix gate (PR-2).

Validates the frozen train->test evaluation matrix and enforces that cross-domain
performance is honestly recorded as degradation, not capability. It also checks the
in-domain headline is consistent with the frozen result artifact, and that the
TF-IDF leakage collapse (high in-domain -> chance cross-corpus) is present as the
contamination proof.

Writes ``artifacts/verification/CROSS_DOMAIN_MATRIX.json``; emits
``CROSS_DOMAIN_MATRIX_PASS``. Exits non-zero on a missing matrix or a dishonest cell
(a cross-domain cell claiming performance at/above its in-domain counterpart).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "research" / "cogveritas" / "cross_domain_matrix.json"
RESULTS = ROOT / "research" / "cogveritas" / "phase0_results.json"
OUT = ROOT / "artifacts" / "verification" / "CROSS_DOMAIN_MATRIX.json"

# The contamination proof is high in-domain -> chance cross-corpus. The in-domain
# leakage model must be genuinely HIGH for the collapse to mean anything (chance ->
# chance proves nothing). Pinned in the checker, not read from the audited file.
_TFIDF_INDOMAIN_FLOOR = 0.85
# Sane envelope the declared chance_band must sit inside, so the audited artifact
# cannot widen its own passing band to force a collapse verdict.
_CHANCE_BAND_ENVELOPE = (0.40, 0.60)


def _f(x: object) -> float:
    return float(x) if isinstance(x, (int, float, str)) else 0.0


def check() -> tuple[dict[str, object], list[str]]:
    if not MATRIX.is_file():
        return {}, [f"missing cross-domain matrix: {MATRIX.relative_to(ROOT)}"]
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    problems: list[str] = []
    if not cells:
        problems.append("cross-domain matrix has no cells")

    # Group by model; the in-domain cell is the reference for degradation.
    by_model: dict[str, list[dict[str, object]]] = {}
    for c in cells:
        by_model.setdefault(str(c.get("model", "")), []).append(c)

    for model, rows in by_model.items():
        in_domain = next((r for r in rows if "in-domain" in str(r.get("regime", ""))), None)
        if in_domain is None:
            continue
        ref = _f(in_domain.get("roc_auc"))
        for r in rows:
            regime = str(r.get("regime", ""))
            auc = _f(r.get("roc_auc"))
            if "cross" in regime and auc > ref + 1e-9:
                problems.append(f"{model}: cross-domain {regime} AUC {auc} exceeds in-domain {ref} (not degradation)")

    # Required regimes must be present (the honest evidence must not be hidden).
    regimes = {str(c.get("regime", "")) for c in cells}
    for required in ("in-domain", "cross-corpus"):
        if not any(required in reg for reg in regimes):
            problems.append(f"cross-domain matrix omits required regime: {required!r}")
    if not any("high-stakes" in reg for reg in regimes):
        problems.append("cross-domain matrix omits the real high-stakes (RLT) regime")

    # Leakage proof: a high in-domain model must collapse toward chance cross-corpus.
    # This is the central contamination evidence and is MANDATORY — it must not be
    # silently skippable by dropping the ceiling rows from the audited file.
    env_lo, env_hi = _CHANCE_BAND_ENVELOPE
    lo, hi = data.get("chance_band", [0.45, 0.58])
    lo_f, hi_f = _f(lo), _f(hi)
    if not (env_lo <= lo_f < hi_f <= env_hi):
        problems.append(
            f"declared chance_band {[lo_f, hi_f]} outside pinned envelope {list(_CHANCE_BAND_ENVELOPE)} "
            "(audited file cannot define its own passing band)"
        )
    tfidf = by_model.get("tf-idf-ceiling", [])
    tf_in = next((r for r in tfidf if "in-domain" in str(r.get("regime", ""))), None)
    tf_cross = next((r for r in tfidf if "cross" in str(r.get("regime", ""))), None)
    if tf_in is None or tf_cross is None:
        problems.append(
            "contamination proof absent: tf-idf-ceiling must have both in-domain and "
            "cross-corpus rows (the leakage collapse cannot be omitted)"
        )
    else:
        tf_in_auc = _f(tf_in.get("roc_auc"))
        tf_cross_auc = _f(tf_cross.get("roc_auc"))
        if tf_in_auc < _TFIDF_INDOMAIN_FLOOR:
            problems.append(
                f"tf-idf-ceiling in-domain AUC {tf_in_auc} below leakage floor "
                f"{_TFIDF_INDOMAIN_FLOOR} (collapse is not high->chance, proves nothing)"
            )
        if not (lo_f <= tf_cross_auc <= hi_f):
            problems.append("TF-IDF ceiling does not collapse toward chance cross-corpus (leakage proof missing)")

    # Consistency with the frozen result artifact for the in-domain headline.
    if RESULTS.is_file():
        res = json.loads(RESULTS.read_text(encoding="utf-8"))
        headline = next((r for r in res.get("results", []) if "verbal-science" in str(r.get("model", ""))), None)
        vs_in = next(
            (r for r in by_model.get("verbal-science", []) if r.get("regime") == "in-domain"), None
        )
        if headline and vs_in and abs(_f(headline.get("roc_auc")) - _f(vs_in.get("roc_auc"))) > 0.01:
            problems.append("matrix in-domain AUC disagrees with the frozen result artifact")

    artifact = {
        "chance_band": data.get("chance_band"),
        "cells": cells,
        "models": sorted(by_model),
        "regimes": sorted(regimes),
        "problems": problems,
        "status": "PASS" if not problems else "FAIL",
    }
    return artifact, problems


def main() -> int:
    artifact, problems = check()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if artifact:
        OUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if problems:
        for p in problems:
            print(f"CROSS_DOMAIN_MATRIX_ISSUE {p}")
        print(f"CROSS_DOMAIN_MATRIX_FAIL {len(problems)} issue(s)")
        return 1
    print("CROSS_DOMAIN_MATRIX_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
