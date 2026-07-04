"""Mutation-check gate — proves the core tests can FAIL on a real defect (A3, A4).

Coverage is visibility, not correctness. This applies known semantic mutations to
the crown-jewel invariants (no-verdict / forbidden-judgment scan, out-of-domain
probability suppression, opinion-not-checkable) and asserts each is KILLED — the
covering test must fail. A mutation the suite does not catch is a SURVIVOR: a hole
in the evidence, named explicitly. The gate fails if any critical mutation survives.

Each mutation patches the real source, runs the real covering test, and reverts in a
`finally` so the tree is never left mutated. Writes
``artifacts/verification/MUTATION_SCORE.json``; emits ``MUTATION_SCORE_PASS``.

Institutional-verify only — it mutates source during the run and must never execute
inside verify_release's battery.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "verification" / "MUTATION_SCORE.json"


@dataclass(frozen=True)
class Mutation:
    id: str
    invariant: str
    file: str
    old: str
    new: str
    killer_test: str


_MUTATIONS = (
    Mutation(
        id="disable_forbidden_judgment_scan",
        invariant="no person-level judgment in system framing",
        file="src/bive/cogveritas/output_contract.py",
        old="        hits = _scan_system_framing(self)\n        if hits:",
        new="        hits = _scan_system_framing(self)\n        if hits and False:",
        killer_test="tests/test_cogveritas.py::test_no_forbidden_person_level_strings",
    ),
    Mutation(
        id="let_probability_escape_out_of_domain",
        invariant="unsupported probability suppressed (ECE gate)",
        file="src/bive/cogveritas/output_contract.py",
        old="    if ece is None or ece >= ECE_THRESHOLD:",
        new="    if False:",
        killer_test="tests/test_cogveritas.py::test_no_float_probability_when_ece_fails",
    ),
    Mutation(
        id="classify_everything_checkable",
        invariant="opinion is not externally checkable",
        file="src/bive/cogveritas/verifiability_tagger.py",
        old="    return \"not_externally_checkable\"",
        new="    return \"externally_checkable\"",
        killer_test="tests/test_cogveritas_lang.py::test_opinion_markers_are_language_specific",
    ),
)


def _run_killer(test: str) -> bool:
    """True if the covering test FAILS (mutant killed)."""
    proc = subprocess.run(  # noqa: S603 - fixed in-repo test id
        [sys.executable, "-m", "pytest", test, "-x", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1", "PATH": _path()},
    )
    return proc.returncode != 0


def _path() -> str:
    import os  # noqa: PLC0415

    return os.environ.get("PATH", "")


def _apply(mut: Mutation) -> str:
    """Return 'killed' / 'survived' / 'invalid_mutation'. Always reverts the source."""
    path = ROOT / mut.file
    original = path.read_text(encoding="utf-8")
    if mut.old not in original:
        return "invalid_mutation"  # target drifted — mutation cannot be trusted
    try:
        path.write_text(original.replace(mut.old, mut.new, 1), encoding="utf-8")
        return "killed" if _run_killer(mut.killer_test) else "survived"
    finally:
        path.write_text(original, encoding="utf-8")


def run() -> dict[str, object]:
    results = []
    for mut in _MUTATIONS:
        outcome = _apply(mut)
        results.append({"id": mut.id, "invariant": mut.invariant, "killer_test": mut.killer_test, "outcome": outcome})
    survivors = [r["id"] for r in results if r["outcome"] != "killed"]
    killed = sum(1 for r in results if r["outcome"] == "killed")
    return {
        "mutations": results,
        "total": len(results),
        "killed": killed,
        "survivors": survivors,
        "kill_ratio": round(killed / len(results), 3) if results else 0.0,
        "status": "PASS" if not survivors else "FAIL",
    }


def main() -> int:
    report = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report["survivors"]:
        for s in report["survivors"]:  # type: ignore[attr-defined]
            print(f"MUTATION_SURVIVOR {s} — a critical invariant is not defended by tests")
        print(f"MUTATION_SCORE_FAIL {len(report['survivors'])} survivor(s)")  # type: ignore[arg-type]
        return 1
    print(f"MUTATION_SCORE_PASS {report['killed']}/{report['total']} critical mutations killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
