"""PR-5 Misuse Threat Model + PR-6 External Replication gates (hardened)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import external_replication_check as er  # noqa: E402  (needs scripts/ on sys.path first)
import misuse_threat_model_check as mt  # noqa: E402


def test_misuse_threat_model_live_passes() -> None:
    assert mt.check() == []


def test_misuse_model_covers_all_ten_required_risks() -> None:
    text = mt.DOC.read_text(encoding="utf-8").lower()
    assert len(mt._REQUIRED_RISKS) == 10
    for risk in mt._REQUIRED_RISKS:
        assert risk in text, f"missing risk: {risk}"


def test_misuse_safeguards_point_to_real_mechanisms() -> None:
    for _label, rel in mt._MECHANISMS.items():
        assert (mt.ROOT / rel).is_file(), f"safeguard mechanism missing: {rel}"


def test_misuse_gate_emits_audit_artifact() -> None:
    assert mt.main() == 0
    art = json.loads(mt.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert art["risk_count"] == 10


def test_misuse_doc_lives_under_security() -> None:
    assert mt.DOC.as_posix().endswith("docs/security/MISUSE_THREAT_MODEL.md")


def test_external_replication_live_ready() -> None:
    assert er.check() == []


def test_external_gate_emits_readiness_artifact_not_replicated() -> None:
    assert er.main() == 0
    art = json.loads(er.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    # Honesty: readiness is not the same as an actual third-party replication.
    assert art["externally_replicated"] is False
    assert art["readiness"] == "ready"


def test_replication_requires_all_assets() -> None:
    for asset in er._REQUIRED_ASSETS:
        assert (er.RESEARCH / asset).is_file(), f"missing replication asset: {asset}"
