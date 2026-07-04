"""PR-3 Resource-Effectiveness Audit — cost + posture, on the FULL battery timing.

Tests use controlled synthetic timing (never the live, possibly-mid-run artifact),
and include mutation proof that the budget and completeness checks actually FAIL on a
real defect — otherwise the gate would be decoration (A3).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import resource_effectiveness_check as re_check  # noqa: E402  (needs scripts/ on sys.path first)


def _timing(tmp_path: Path, gates: list[dict[str, object]]) -> Path:
    p = tmp_path / "RELEASE_TIMINGS.json"
    p.write_text(json.dumps({"gates": gates, "gate_count": len(gates), "status": "pass"}), encoding="utf-8")
    return p


def _ok_gates(n: int) -> list[dict[str, object]]:
    return [{"name": f"g{i}", "duration_seconds": 1.0, "result": "pass"} for i in range(n)]


def test_complete_passing_battery_reports_all_fields(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(re_check, "_expected_gate_count", lambda: 46)
    monkeypatch.setattr(re_check, "GATES", _timing(tmp_path, _ok_gates(46)))
    report, problems = re_check.audit()
    assert problems == []
    for field in ("total_seconds", "memory_policy", "dependencies", "test_count", "gate_count", "artifacts_present", "expensive_failures"):
        assert field in report


def test_incomplete_battery_fails(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(re_check, "_expected_gate_count", lambda: 46)
    monkeypatch.setattr(re_check, "GATES", _timing(tmp_path, _ok_gates(4)))  # only 4 of 46
    _report, problems = re_check.audit()
    assert any("incomplete timing" in p for p in problems)


def test_budget_bites_on_slow_gate(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Mutation proof: a gate exceeding the per-gate budget must FAIL the audit.
    monkeypatch.setattr(re_check, "_expected_gate_count", lambda: 1)
    slow = [{"name": "bloated", "duration_seconds": re_check._PER_GATE_BUDGET_S + 1, "result": "pass"}]
    monkeypatch.setattr(re_check, "GATES", _timing(tmp_path, slow))
    _report, problems = re_check.audit()
    assert any("per-gate budget" in p for p in problems)


def test_failed_gate_in_timing_fails(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(re_check, "_expected_gate_count", lambda: 1)
    gates = [{"name": "broken", "duration_seconds": 1.0, "result": "fail"}]
    monkeypatch.setattr(re_check, "GATES", _timing(tmp_path, gates))
    _report, problems = re_check.audit()
    assert any("not recorded as pass" in p for p in problems)


def test_blank_result_is_not_a_silent_pass(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The fail-open this replaces: a missing/empty result must NOT count as passing.
    monkeypatch.setattr(re_check, "_expected_gate_count", lambda: 1)
    gates = [{"name": "unmarked", "duration_seconds": 1.0}]  # no "result" key
    monkeypatch.setattr(re_check, "GATES", _timing(tmp_path, gates))
    _report, problems = re_check.audit()
    assert any("not recorded as pass" in p for p in problems), problems


def test_zero_duration_is_unmeasured_not_free(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # A gate with no measured time is unmeasured, not a free pass.
    monkeypatch.setattr(re_check, "_expected_gate_count", lambda: 1)
    gates = [{"name": "instant", "duration_seconds": 0.0, "result": "pass"}]
    monkeypatch.setattr(re_check, "GATES", _timing(tmp_path, gates))
    _report, problems = re_check.audit()
    assert any("no measured duration" in p for p in problems), problems


def test_all_blank_battery_does_not_pass(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The exact theater: a complete-count artifact of empty entries must fail, not PASS.
    monkeypatch.setattr(re_check, "_expected_gate_count", lambda: 3)
    gates: list[dict[str, object]] = [{"name": f"g{i}"} for i in range(3)]
    monkeypatch.setattr(re_check, "GATES", _timing(tmp_path, gates))
    _report, problems = re_check.audit()
    assert problems, "an all-blank timing artifact must not pass the resource audit"


def test_missing_timing_artifact_fails_closed(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(re_check, "GATES", tmp_path / "absent.json")
    report, problems = re_check.audit()
    assert report == {} and problems


def test_expected_gate_count_is_the_full_battery() -> None:
    assert re_check._expected_gate_count() >= 40
