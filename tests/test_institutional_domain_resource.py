"""PR-2 Domain-Distance + PR-3 Resource-Effectiveness gates."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import domain_distance_check as dd  # noqa: E402  (needs scripts/ on sys.path first)
import resource_effectiveness_check as re_check  # noqa: E402


def test_domain_distance_live_passes() -> None:
    # The methodology contract + empirical doc must distinguish regimes.
    assert dd.check() == []


def test_domain_distance_requires_regime_labels() -> None:
    # The contract's findings must all carry a regime label (guards the gate's core).
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from bive.cogveritas.methodology import methodology_contract

    findings = methodology_contract()["findings"]
    assert findings and all(str(f.get("regime", "")).strip() for f in findings)


def test_resource_report_within_budget_when_timing_present() -> None:
    report, problems = re_check.audit()
    if not report:  # timing artifact absent in a bare checkout — acceptable
        assert problems
        return
    assert float(report["total_seconds"]) <= float(report["total_budget_seconds"])  # type: ignore[arg-type]
    assert int(report["gate_count"]) >= 1  # type: ignore[arg-type]


def test_resource_budget_constants_are_bounded() -> None:
    assert 0 < re_check._PER_GATE_BUDGET_S <= re_check._TOTAL_BUDGET_S
