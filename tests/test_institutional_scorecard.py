"""PR-7 Institutional Scorecard — maturity computed only from gates, honestly capped."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import institutional_scorecard as sc  # noqa: E402  (needs scripts/ on sys.path first)


def test_weights_sum_to_100() -> None:
    assert sum(w for _n, w, _s in sc._DIMENSIONS) == 100


def test_score_is_gate_derived_no_manual_override() -> None:
    card = sc.compute()
    assert card["computed_from_gates"] is True
    assert card["manual_override"] is False


def test_band_is_capped_below_benchmark_grade_without_replication() -> None:
    # The top band requires actual third-party replication, which cannot be
    # self-certified. Even a perfect raw score must not reach benchmark-grade.
    card = sc.compute()
    assert card["externally_replicated"] is False
    assert float(card["score"]) <= sc._UNREPLICATED_CAP  # type: ignore[arg-type]
    assert "benchmark-grade" not in str(card["band"])


def test_score_never_exceeds_raw() -> None:
    card = sc.compute()
    assert float(card["score"]) <= float(card["raw_score"])  # type: ignore[arg-type]


def test_gate_emits_artifact() -> None:
    assert sc.main() == 0
    art = json.loads(sc.OUT.read_text(encoding="utf-8"))
    assert art["manual_override"] is False
    assert art["dimensions"]


_FULL_LOG = (
    "VERIFY_GATE_PASS threat-model\n"
    "VERIFY_GATE_PASS security-static\n"
    "VERIFY_GATE_PASS misuse-threat-model\n"
    "VERIFY_GATE_PASS product-claim-audit\n"
    "VERIFY_RELEASE_PASS\n"
)


def _sandbox(tmp_path: Path, log_contents: str | None) -> Path:
    """A repo-shaped tmp dir where release_governance's file checks pass; the log is
    written only if `log_contents` is given (None => no recorded run)."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "verify_release.py").write_text("", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("", encoding="utf-8")
    if log_contents is not None:
        verif = tmp_path / "artifacts" / "verification"
        verif.mkdir(parents=True)
        (verif / "VERIFY_RELEASE.log").write_text(log_contents, encoding="utf-8")
    return tmp_path


def _governance(tmp_path: Path, monkeypatch, log_contents: str | None) -> bool:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(sc, "ROOT", _sandbox(tmp_path, log_contents))
    return sc._proxy("release_governance")


def test_release_governance_fails_without_log(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Files exist, but no recorded release run -> the dimension must NOT be earned.
    assert _governance(tmp_path, monkeypatch, None) is False


def test_release_governance_fails_when_a_governance_gate_did_not_pass(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # A complete, terminal-PASS run MISSING one governance gate's pass line must not
    # earn the dimension — existence of the run is not enough.
    partial = _FULL_LOG.replace("VERIFY_GATE_PASS security-static\n", "")
    assert _governance(tmp_path, monkeypatch, partial) is False


def test_release_governance_fails_on_recorded_gate_failure(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    failed = _FULL_LOG.replace("VERIFY_RELEASE_PASS\n", "VERIFY_GATE_FAIL security-static\n")
    assert _governance(tmp_path, monkeypatch, failed) is False


def test_release_governance_passes_on_full_governance_evidence(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    assert _governance(tmp_path, monkeypatch, _FULL_LOG) is True
