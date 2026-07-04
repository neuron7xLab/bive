"""Regression: institutional-verify must never print an unearned base sentinel.

Guards the fix for the defect where COGVERITAS_VERIFY_COMPLETE and VERIFY_RELEASE_PASS
were printed unconditionally — i.e. faked when the release battery had not run. The
base battery is verified from verify-release's OWN log (VERIFY_RELEASE.log): terminal
pass, no failed gate, and a complete count of VERIFY_GATE_PASS lines.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import institutional_verify as iv  # noqa: E402  (needs scripts/ on sys.path first)


def _log(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "VERIFY_RELEASE.log"
    p.write_text(text, encoding="utf-8")
    return p


def _complete(n: int) -> str:
    return "\n".join(f"VERIFY_GATE_PASS gate{i}" for i in range(n)) + "\nVERIFY_RELEASE_PASS\n"


def test_absent_log_is_unverified(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(iv, "_VR_LOG", tmp_path / "nope.log")
    ok, reason = iv._base_battery_status()
    assert ok is False and "absent" in reason


def test_failed_gate_in_log_is_unverified(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(iv, "_expected_gate_count", lambda: 3)
    monkeypatch.setattr(iv, "_VR_LOG", _log(tmp_path, "VERIFY_GATE_PASS a\nVERIFY_GATE_FAIL b\nVERIFY_RELEASE_FAIL\n"))
    ok, _ = iv._base_battery_status()
    assert ok is False


def test_incomplete_run_is_unverified(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(iv, "_expected_gate_count", lambda: 46)
    monkeypatch.setattr(iv, "_VR_LOG", _log(tmp_path, _complete(4)))  # only 4 gate passes
    ok, reason = iv._base_battery_status()
    assert ok is False and "incomplete" in reason


def test_no_terminal_pass_is_unverified(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(iv, "_expected_gate_count", lambda: 3)
    monkeypatch.setattr(iv, "_VR_LOG", _log(tmp_path, "VERIFY_GATE_PASS a\nVERIFY_GATE_PASS b\nVERIFY_GATE_PASS c\n"))
    ok, _ = iv._base_battery_status()
    assert ok is False  # no VERIFY_RELEASE_PASS terminal line


def test_complete_all_passing_run_is_verified(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(iv, "_expected_gate_count", lambda: 3)
    monkeypatch.setattr(iv, "_VR_LOG", _log(tmp_path, _complete(3)))
    ok, reason = iv._base_battery_status()
    assert ok is True and reason == ""


def test_expected_gate_count_reads_release_battery() -> None:
    # The completeness threshold is derived from the real release battery, not hardcoded.
    assert iv._expected_gate_count() >= 40
