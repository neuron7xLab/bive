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
