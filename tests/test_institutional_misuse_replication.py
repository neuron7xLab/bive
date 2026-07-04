"""PR-5 Misuse Threat Model + PR-6 External Replication gates."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import external_replication_check as er  # noqa: E402  (needs scripts/ on sys.path first)
import misuse_threat_model_check as mt  # noqa: E402


def test_misuse_threat_model_live_passes() -> None:
    assert mt.check() == []


def test_misuse_model_covers_required_scenarios() -> None:
    text = mt.DOC.read_text(encoding="utf-8").lower()
    for scenario in mt._REQUIRED_SCENARIOS:
        assert scenario in text, f"missing scenario: {scenario}"


def test_misuse_safeguards_point_to_real_mechanisms() -> None:
    # Every cited mechanism file must exist (a safeguard pointing nowhere is theatre).
    for _label, rel in mt._MECHANISMS.items():
        assert (mt.ROOT / rel).is_file(), f"safeguard mechanism missing: {rel}"


def test_external_replication_live_ready() -> None:
    assert er.check() == []


def test_replication_requires_all_assets() -> None:
    for asset in er._REQUIRED_ASSETS:
        assert (er.RESEARCH / asset).is_file(), f"missing replication asset: {asset}"
