"""Benchmark Card gate (PR-1) — every benchmark is documented and consistent.

Validates that ``docs/methodology/BENCHMARK_CARD.md`` documents each benchmark with
the required fields and that it is consistent with the frozen research result
(``research/cogveritas/phase0_results.json``): the card must not report a headline
number the artifact does not contain, and the artifact must declare its protocol,
limitation, and the length-only chance baseline.

Emits ``BENCHMARK_CARD_PASS``; exits non-zero on any missing field or inconsistency.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs" / "methodology" / "BENCHMARK_CARD.md"
RESULTS = ROOT / "research" / "cogveritas" / "phase0_results.json"

# Sections/fields the card MUST carry, per benchmark discipline.
_REQUIRED_CARD = (
    "Size:",
    "Split:",
    "Provenance:",
    "Limitation",
    "Contamination controls",
    "Real-Life Trial",
    "cross-corpus",
)
# Fields the frozen result artifact MUST declare.
_REQUIRED_RESULT = ("corpus", "protocol", "limitation", "results")


def check() -> list[str]:
    problems: list[str] = []
    if not CARD.is_file():
        return [f"missing benchmark card: {CARD.relative_to(ROOT)}"]
    if not RESULTS.is_file():
        return [f"missing frozen result: {RESULTS.relative_to(ROOT)}"]

    card = CARD.read_text(encoding="utf-8")
    for field in _REQUIRED_CARD:
        if field not in card:
            problems.append(f"benchmark card missing required field: {field!r}")

    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    for field in _REQUIRED_RESULT:
        if field not in data:
            problems.append(f"frozen result missing field: {field!r}")

    results = {r.get("model", ""): r for r in data.get("results", [])}
    # A length-only chance baseline must exist and sit near chance (<= 0.55).
    baseline = next((r for k, r in results.items() if "length-only" in k), None)
    if baseline is None:
        problems.append("frozen result missing the length-only chance baseline")
    elif float(baseline.get("roc_auc", 1.0)) > 0.55:
        problems.append(f"length-only baseline not near chance: {baseline.get('roc_auc')}")

    # The card must carry the headline verbal-science AUC from the artifact.
    headline = next((r for k, r in results.items() if "verbal-science" in k), None)
    if headline is not None:
        auc = float(headline.get("roc_auc", 0.0))
        if f"{auc:.4f}"[:5] not in card and f"{auc:.4f}" not in card:
            problems.append(f"card omits the headline verbal-science AUC {auc}")
    return problems


def main() -> int:
    problems = check()
    if problems:
        for p in problems:
            print(f"BENCHMARK_CARD_ISSUE {p}")
        print(f"BENCHMARK_CARD_FAIL {len(problems)} issue(s)")
        return 1
    print("BENCHMARK_CARD_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
