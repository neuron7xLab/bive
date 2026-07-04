"""PR-3 Resource-Effectiveness Audit — cost + posture reporting."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import resource_effectiveness_check as re_check  # noqa: E402  (needs scripts/ on sys.path first)


def test_report_declares_all_mandated_fields() -> None:
    report, problems = re_check.audit()
    if not report:  # no timing artifact in a bare checkout — must fail closed
        assert problems
        return
    # The mandate requires wall time, memory policy, dependencies, tests, gates,
    # artifacts, and expensive failures.
    for field in (
        "total_seconds", "memory_policy", "dependencies", "test_count",
        "gate_count", "artifacts_present", "expensive_failures",
    ):
        assert field in report, f"resource report omits {field}"


def test_report_within_budget_and_no_expensive_failures() -> None:
    report, _ = re_check.audit()
    if not report:
        return
    assert float(report["total_seconds"]) <= float(report["total_budget_seconds"])  # type: ignore[arg-type]
    assert report["expensive_failures"] == []  # a non-passing gate would fail the audit


def test_counts_are_non_negative() -> None:
    assert re_check._dependency_count() >= 0
    assert re_check._test_count() >= 1


def test_gate_emits_artifact() -> None:
    assert re_check.main() == 0
    art = json.loads(re_check.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert "memory_policy" in art
