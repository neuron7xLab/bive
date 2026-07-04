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
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs" / "methodology" / "BENCHMARK_CARD.md"
RESULTS = ROOT / "research" / "cogveritas" / "phase0_results.json"
MATRIX = ROOT / "research" / "cogveritas" / "cross_domain_matrix.json"
OUT = ROOT / "artifacts" / "verification" / "BENCHMARK_CARD.json"
_LEAK_LINE = 0.85
# Documented policy constants the card may cite that are not experiment results.
_POLICY_CONSTANTS = (0.85, 0.50)
# A number claimed adjacent to the token "AUC" is a headline claim (before or after,
# through bold/space/=/:/≥). CI bounds in [..] and ECE follow other tokens and are
# deliberately NOT captured.
_AUC_CLAIM = re.compile(r"AUC[\s*=:≥>]*?(0\.\d{2,4})|(0\.\d{2,4})[\s*=:]*?AUC", re.IGNORECASE)

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

    # The card must carry the headline verbal-science AUC from the artifact. The
    # headline result is load-bearing — it MUST exist, not merely be checked-if-present
    # (renaming it away must not silently skip the consistency proof).
    headline = next((r for k, r in results.items() if "verbal-science" in k), None)
    if headline is None:
        problems.append("frozen result missing the headline verbal-science entry")
    else:
        auc = float(headline.get("roc_auc", 0.0))
        if f"{auc:.4f}"[:5] not in card and f"{auc:.4f}" not in card:
            problems.append(f"card omits the headline verbal-science AUC {auc}")

    # Reverse direction (the docstring's promise): the card must NOT report an AUC the
    # frozen artifacts do not contain. Build the allowed set from every frozen research
    # AUC plus documented policy constants; flag any AUC-adjacent claim outside it.
    allowed = _allowed_auc_strings(data)
    for claimed in _card_auc_claims(card):
        if claimed not in allowed:
            problems.append(f"card reports AUC {claimed} absent from the frozen artifacts")
    return problems


def _auc_strings(value: object) -> set[str]:
    """A numeric AUC rendered at 2/3/4 decimal places (the card uses mixed precision)."""
    if not isinstance(value, (int, float)):
        return set()
    return {f"{float(value):.{dp}f}" for dp in (2, 3, 4)}


def _allowed_auc_strings(results_data: dict[str, object]) -> set[str]:
    allowed: set[str] = set()
    rows = results_data.get("results", [])
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict):
                allowed |= _auc_strings(r.get("roc_auc"))
    if MATRIX.is_file():
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cells = matrix.get("cells", []) if isinstance(matrix, dict) else []
        if isinstance(cells, list):
            for cell in cells:
                if isinstance(cell, dict):
                    allowed |= _auc_strings(cell.get("roc_auc"))
    for c in _POLICY_CONSTANTS:
        allowed |= _auc_strings(c)
    return allowed


def _card_auc_claims(card: str) -> set[str]:
    return {m.group(1) or m.group(2) for m in _AUC_CLAIM.finditer(card)}


def _card_artifact(problems: list[str]) -> dict[str, object]:
    """Machine-readable benchmark card derived from the frozen result."""
    benchmarks: list[dict[str, object]] = []
    if RESULTS.is_file():
        data = json.loads(RESULTS.read_text(encoding="utf-8"))
        rows = []
        for r in data.get("results", []):
            auc = r.get("roc_auc")
            rows.append(
                {
                    "model": r.get("model", ""),
                    "roc_auc": auc,
                    "ece": r.get("ece"),
                    "contamination_flag": bool(isinstance(auc, (int, float)) and auc >= _LEAK_LINE),
                }
            )
        benchmarks.append(
            {
                "corpus": data.get("corpus", ""),
                "protocol": data.get("protocol", ""),
                "limitation": data.get("limitation", ""),
                "results": rows,
            }
        )
    return {
        "card_doc": "docs/methodology/BENCHMARK_CARD.md",
        "leakage_line": _LEAK_LINE,
        "benchmarks": benchmarks,
        "issues": problems,
        "status": "PASS" if not problems else "FAIL",
    }


def main() -> int:
    problems = check()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(_card_artifact(problems), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if problems:
        for p in problems:
            print(f"BENCHMARK_CARD_ISSUE {p}")
        print(f"BENCHMARK_CARD_FAIL {len(problems)} issue(s)")
        return 1
    print(f"BENCHMARK_CARD_PASS artifact={OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
