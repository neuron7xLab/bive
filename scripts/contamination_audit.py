"""Contamination Audit gate (PR-1) — enforce the leakage rule.

The governing rule from the empirical validation: *any headline ROC-AUC >= 0.85 is
assumed to be leakage until proven to transfer cross-corpus.* This audit scans the
frozen result artifact and the empirical docs and BLOCKS the release if a high AUC
appears without a leakage / ceiling / cross-corpus qualifier in its context — i.e.
if a contaminated headline is presented as a capability.

Emits ``CONTAMINATION_AUDIT_PASS``; exits non-zero on any un-qualified high headline.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "cogveritas" / "phase0_results.json"
_DOCS = (
    "docs/EMPIRICAL_VALIDATION.md",
    "docs/methodology/BENCHMARK_CARD.md",
    "research/cogveritas/PHASE0_REPORT.md",
)

_LEAK_THRESHOLD = 0.85
# Context words that correctly frame a high number as not-a-capability.
_QUALIFIERS = ("ceiling", "leakage", "cross-corpus", "collapse", "tf-idf", "tf–idf", "contamination", "0.51", "0.510")
# AUC-like numbers in prose (0.xx or 0.xxx).
_AUC = re.compile(r"\b0\.(?:8[5-9]|9\d)\d?\b")


def _result_problems() -> list[str]:
    if not RESULTS.is_file():
        return [f"missing frozen result: {RESULTS.relative_to(ROOT)}"]
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    problems: list[str] = []
    for r in data.get("results", []):
        auc = r.get("roc_auc")
        model = str(r.get("model", ""))
        high = isinstance(auc, (int, float)) and auc >= _LEAK_THRESHOLD
        labelled = any(q in model.lower() for q in ("ceiling", "tf-idf", "tf–idf", "leak"))
        if high and not labelled:
            # A high headline must be labelled as a ceiling / tf-idf leakage row.
            problems.append(f"frozen result: AUC {auc} for {model!r} >= {_LEAK_THRESHOLD} without ceiling/leakage label")
    return problems


def unqualified_high_auc(text: str) -> list[int]:
    """Line numbers where a high AUC appears without a leakage/cross-corpus qualifier."""
    hits: list[int] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        if not _AUC.search(line):
            continue
        context = " ".join(lines[max(0, lineno - 3) : lineno + 2]).lower()
        if not any(q in context for q in _QUALIFIERS):
            hits.append(lineno)
    return hits


def _doc_problems() -> list[str]:
    problems: list[str] = []
    for rel in _DOCS:
        path = ROOT / rel
        if not path.is_file():
            continue
        for lineno in unqualified_high_auc(path.read_text(encoding="utf-8")):
            problems.append(f"{rel}:{lineno} high AUC without leakage/cross-corpus context")
    return problems


def audit() -> list[str]:
    return _result_problems() + _doc_problems()


def main() -> int:
    problems = audit()
    if problems:
        for p in problems:
            print(f"CONTAMINATION {p}")
        print(f"CONTAMINATION_AUDIT_FAIL {len(problems)} un-qualified high headline(s)")
        return 1
    print("CONTAMINATION_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
