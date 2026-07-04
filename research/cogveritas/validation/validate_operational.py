"""Operational validation of COGVERITAS on real open data.

This validates what the system ACTUALLY claims — language routing, the no-verdict
invariant, probability suppression, integrity reproducibility, and verifiability
face-validity — on a real, open, labeled corpus (Tatoeba, CC BY 2.0 FR). It does
NOT estimate deception-detection accuracy: the system does not emit a deception
verdict, and passive verbal deception detection is empirically at chance, so such a
metric would be a category error.

Hard invariants (no-verdict, no unproven probability, reproducible integrity) are
FALSIFICATION gates: any violation exits non-zero. Language accuracy and
verifiability face-validity are reported with 95% Wilson confidence intervals.

Writes VALIDATION_REPORT.json next to this script. Run:
    PYTHONPATH=src python research/cogveritas/validation/validate_operational.py
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from bive.cogveritas.lang import detect_language  # noqa: E402
from bive.cogveritas.service import analyze_verifiability  # noqa: E402
from bive.cogveritas.verifiability_tagger import (  # noqa: E402
    classify_claim_verifiability,
    segment_claims,
)

LANG_CORPUS = HERE / "lang_corpus.json"
LANG_HELDOUT = HERE / "lang_heldout.json"
PROBE = HERE / "verifiability_probe.json"
REPORT = HERE / "VALIDATION_REPORT.json"


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion (robust at small n)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def _load(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    sentences: list[dict[str, str]] = data["sentences"]
    return sentences


def _detection_metrics(rows: list[dict[str, str]]) -> dict[str, object]:
    correct = 0
    confusion: Counter[str] = Counter()
    per_lang_total: Counter[str] = Counter()
    per_lang_correct: Counter[str] = Counter()
    for r in rows:
        gold, text = r["gold"], r["text"]
        pred = detect_language(text)
        per_lang_total[gold] += 1
        if pred == gold:
            correct += 1
            per_lang_correct[gold] += 1
        else:
            confusion[f"{gold}->{pred}"] += 1
    n = len(rows)
    per_lang = {
        g: {
            "n": per_lang_total[g],
            "accuracy": round(per_lang_correct[g] / per_lang_total[g], 4),
            "ci95": wilson_ci(per_lang_correct[g], per_lang_total[g]),
        }
        for g in sorted(per_lang_total)
    }
    return {
        "n": n,
        "accuracy": round(correct / n, 4),
        "ci95": wilson_ci(correct, n),
        "per_language": per_lang,
        "confusions": dict(confusion.most_common()),
    }


def validate_hard_invariants() -> tuple[dict[str, object], list[str]]:
    """No-verdict and probability-suppression over EVERY corpus sentence."""
    rows = _load(LANG_CORPUS) + _load(LANG_HELDOUT) + _load(PROBE)
    verdict_violations: list[str] = []
    probability_violations: list[str] = []
    for r in rows:
        out = analyze_verifiability(r["text"])
        if out.verdict is not None:
            verdict_violations.append(r["text"])
        if out.calibrated_probability is not None:
            probability_violations.append(r["text"])
    report = {
        "checked": len(rows),
        "verdict_is_null": len(verdict_violations) == 0,
        "verdict_violations": verdict_violations,
        "probability_suppressed": len(probability_violations) == 0,
        "probability_violations": probability_violations,
    }
    problems: list[str] = []
    if verdict_violations:
        problems.append(f"no-verdict invariant broken on {len(verdict_violations)} input(s)")
    if probability_violations:
        problems.append(f"probability escaped without calibration on {len(probability_violations)} input(s)")
    return report, problems


def validate_integrity_reproducibility() -> tuple[dict[str, object], list[str]]:
    """Same input -> same fingerprint: within a run, and across PYTHONHASHSEED."""
    rows = _load(LANG_CORPUS)[:30]
    problems: list[str] = []
    unstable_in_run = 0
    for r in rows:
        a = analyze_verifiability(r["text"]).integrity
        b = analyze_verifiability(r["text"]).integrity
        if (a.analysis_sha256, a.source_sha256) != (b.analysis_sha256, b.source_sha256):
            unstable_in_run += 1
    if unstable_in_run:
        problems.append(f"integrity hash non-deterministic within a run on {unstable_in_run} input(s)")

    # Cross-seed: a hash-randomised interpreter must produce the same fingerprint.
    sample = rows[0]["text"]
    seed_hashes = []
    for seed in ("0", "1", "2"):
        proc = subprocess.run(  # noqa: S603 - fixed in-repo snippet
            [sys.executable, "-c", _SEED_SNIPPET, sample],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src", "PYTHONHASHSEED": seed, "PATH": _path()},
        )
        seed_hashes.append(proc.stdout.strip())
    cross_seed_stable = len(set(seed_hashes)) == 1 and bool(seed_hashes[0])
    if not cross_seed_stable:
        problems.append(f"integrity hash varies across PYTHONHASHSEED: {seed_hashes}")
    return {
        "sampled": len(rows),
        "deterministic_within_run": unstable_in_run == 0,
        "cross_seed_stable": cross_seed_stable,
        "cross_seed_hashes": seed_hashes,
    }, problems


_SEED_SNIPPET = (
    "import sys; sys.path.insert(0, 'src');"
    "from bive.cogveritas.service import analyze_verifiability;"
    "print(analyze_verifiability(sys.argv[1]).integrity.analysis_sha256)"
)


def _path() -> str:
    import os  # noqa: PLC0415

    return os.environ.get("PATH", "")


def validate_verifiability_face_validity() -> dict[str, object]:
    """Agreement of externally_checkable/not on clearly-labeled exemplars.

    FACE VALIDITY only — a sanity check that clear factual vs opinion sentences are
    routed as intended, not a population accuracy claim.
    """
    rows = _load(PROBE)
    agree = 0
    disagreements: list[dict[str, str]] = []
    for r in rows:
        claims = segment_claims(r["text"])
        pred = classify_claim_verifiability(claims[0]) if claims else "insufficient_context"
        if pred == r["gold"]:
            agree += 1
        else:
            disagreements.append({"text": r["text"], "gold": r["gold"], "pred": pred})
    n = len(rows)
    return {
        "n": n,
        "agreement": round(agree / n, 4),
        "ci95": wilson_ci(agree, n),
        "disagreements": disagreements,
        "caveat": "face-validity sanity check on curated exemplars; not a population estimate",
    }


def _print_detection(split: str, s: dict[str, object]) -> None:
    print(f"LANGUAGE_DETECTION [{split}] accuracy={s['accuracy']} ci95={s['ci95']} n={s['n']}")
    per_language = s["per_language"]
    if isinstance(per_language, dict):
        for g, gs in per_language.items():
            if isinstance(gs, dict):
                print(f"    {g}: {gs['accuracy']} ci95={gs['ci95']} (n={gs['n']})")
    confusions = s["confusions"]
    if isinstance(confusions, dict) and confusions:
        print(f"    confusions: {confusions}")


def main() -> int:
    in_sample = _detection_metrics(_load(LANG_CORPUS))
    held_out = _detection_metrics(_load(LANG_HELDOUT))
    lang: dict[str, object] = {"in_sample": in_sample, "held_out": held_out}
    invariants, inv_problems = validate_hard_invariants()
    integrity, int_problems = validate_integrity_reproducibility()
    verifiability = validate_verifiability_face_validity()

    problems = inv_problems + int_problems
    report = {
        "scope": "operational validation (routing/invariants/determinism/face-validity); NOT deception accuracy",
        "data": {
            "source": "Tatoeba (CC BY 2.0 FR); curated verifiability probe",
            "in_sample_n": len(_load(LANG_CORPUS)),
            "held_out_n": len(_load(LANG_HELDOUT)),
        },
        "language_detection": lang,
        "hard_invariants": invariants,
        "integrity_reproducibility": integrity,
        "verifiability_face_validity": verifiability,
        "falsification_problems": problems,
        "status": "PASS" if not problems else "FAIL",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _print_detection("in_sample", in_sample)
    _print_detection("held_out", held_out)
    print(
        f"NO_VERDICT_INVARIANT {'HOLDS' if invariants['verdict_is_null'] else 'BROKEN'} "
        f"over {invariants['checked']} inputs"
    )
    print(f"PROBABILITY_SUPPRESSION {'HOLDS' if invariants['probability_suppressed'] else 'BROKEN'}")
    print(
        f"INTEGRITY reproducible_in_run={integrity['deterministic_within_run']} "
        f"cross_seed_stable={integrity['cross_seed_stable']}"
    )
    print(
        f"VERIFIABILITY_FACE_VALIDITY agreement={verifiability['agreement']} "
        f"ci95={verifiability['ci95']} n={verifiability['n']} (sanity check, not accuracy)"
    )
    if problems:
        for p in problems:
            print(f"VALIDATION_FALSIFIED {p}")
        print("OPERATIONAL_VALIDATION_FAIL")
        return 1
    print("OPERATIONAL_VALIDATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
