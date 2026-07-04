"""Domain-Distance Enforcement gate (PR-2).

An in-domain metric must never be presented as a general capability. This gate
enforces that:

1. The machine-readable methodology contract reports its findings *per regime*
   (in-domain, cross-corpus, Real-Life Trial), and includes the real high-stakes
   regime whose CI straddles chance — so a client cannot read one headline number.
2. The empirical documentation presents metrics in a regime-labelled table and
   states the graceful-degradation rule (cross-domain -> ordinal flags, not
   probabilities).

Emits ``DOMAIN_DISTANCE_PASS``; exits non-zero if any regime label is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bive.cogveritas.methodology import methodology_contract  # noqa: E402

_DOC = ROOT / "docs" / "EMPIRICAL_VALIDATION.md"
# The regimes that MUST be distinguished, by keyword.
_REGIMES = ("in-domain", "cross-corpus", "real-life trial")
# Cross-domain honesty: probabilities are not emitted out of domain.
_DEGRADATION = ("ordinal", "not probab", "no probab", "cross-domain")


def check() -> list[str]:
    problems: list[str] = []

    contract = methodology_contract()
    findings = contract.get("findings", [])
    if not findings:
        problems.append("methodology contract has no findings")
    # Every finding must name its regime; and the chance-level real regime must appear.
    for f in findings:
        if not str(f.get("regime", "")).strip():
            problems.append(f"finding without a regime label: {f!r}")
    regimes_text = " ".join(str(f.get("regime", "")).lower() for f in findings)
    if "real-life trial" not in regimes_text and "real high-stakes" not in regimes_text:
        problems.append("methodology contract omits the real high-stakes (RLT) regime")
    if "chance" not in " ".join(str(f.get("reads", "")).lower() for f in findings):
        problems.append("methodology contract never states a regime reads as chance")

    if not _DOC.is_file():
        problems.append(f"missing empirical doc: {_DOC.relative_to(ROOT)}")
    else:
        doc = _DOC.read_text(encoding="utf-8").lower()
        for regime in _REGIMES:
            if regime not in doc:
                problems.append(f"empirical doc omits regime: {regime!r}")
        if not any(k in doc for k in _DEGRADATION):
            problems.append("empirical doc omits the cross-domain degradation rule (ordinal, not probabilities)")
    return problems


def main() -> int:
    problems = check()
    if problems:
        for p in problems:
            print(f"DOMAIN_DISTANCE_ISSUE {p}")
        print(f"DOMAIN_DISTANCE_FAIL {len(problems)} issue(s)")
        return 1
    print("DOMAIN_DISTANCE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
