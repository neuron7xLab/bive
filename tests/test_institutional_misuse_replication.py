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


def test_misuse_has_one_block_per_required_risk() -> None:
    assert len(mt._risk_blocks(mt.DOC.read_text(encoding="utf-8"))) == len(mt._REQUIRED_RISKS)


def test_missing_mitigation_in_one_risk_block_fails(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Drop the mitigation label from the over-reliance block (not the no-verdict one).
    text = mt.DOC.read_text(encoding="utf-8").replace(
        "**Mitigation:** `human_in_the_loop`", "**Note:** `human_in_the_loop`", 1
    )
    doc = tmp_path / "MISUSE.md"
    doc.write_text(text, encoding="utf-8")
    monkeypatch.setattr(mt, "DOC", doc)
    problems = mt.check()
    assert any("over-reliance" in p and "records no mitigation" in p for p in problems), problems


def test_occurrence_stuffing_no_longer_passes(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The exact theater this replaces: strip the per-risk labels but stuff the words
    # globally. The old count-based gate passed; per-risk mapping must now fail.
    text = mt.DOC.read_text(encoding="utf-8")
    stripped = text.replace("**Mitigation:**", "**Xitigation:**").replace(
        "**Residual risk:**", "**Xesidual risk:**"
    )
    stuffed = stripped + "\n\n" + "\n".join(["mitigation: filler; residual risk: filler"] * 12)
    doc = tmp_path / "MISUSE.md"
    doc.write_text(stuffed, encoding="utf-8")
    monkeypatch.setattr(mt, "DOC", doc)
    problems = mt.check()
    assert any("records no mitigation" in p for p in problems), problems


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


# --- existence is not readiness: a stub asset must fail ---


def test_empty_python_asset_is_a_stub() -> None:
    assert er._py_stub_reason("") is not None
    assert er._py_stub_reason("# just a comment\n\n\n") is not None


def test_notimplemented_only_module_is_a_stub() -> None:
    src = (
        "import os\nimport sys\n\n"
        "def run():\n    raise NotImplementedError\n\n"
        "def load():\n    raise NotImplementedError('todo')\n\n"
        "def audit():\n    ...\n"
    )
    assert er._py_stub_reason(src) == "every function is a stub (pass/.../NotImplementedError)"


def test_real_python_asset_is_not_a_stub() -> None:
    for asset in er._PY_ENTRYPOINTS:
        src = (er.RESEARCH / asset).read_text(encoding="utf-8")
        assert er._py_stub_reason(src) is None, f"{asset} misclassified as stub"


def test_empty_shell_asset_is_a_stub() -> None:
    assert er._sh_stub_reason("#!/bin/sh\n# nothing here\n") is not None


def test_real_shell_asset_is_not_a_stub() -> None:
    src = (er.RESEARCH / "fetch_data.sh").read_text(encoding="utf-8")
    assert er._sh_stub_reason(src) is None


def test_check_fails_when_an_entrypoint_is_a_stub(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Full asset set present, but evaluate.py is a NotImplementedError stub -> not ready.
    research = tmp_path / "research" / "cogveritas"
    research.mkdir(parents=True)
    for asset in er._REQUIRED_ASSETS:
        (research / asset).write_text((er.RESEARCH / asset).read_text(encoding="utf-8"), encoding="utf-8")
    (research / "evaluate.py").write_text(
        "def main():\n    raise NotImplementedError\n", encoding="utf-8"
    )
    monkeypatch.setattr(er, "RESEARCH", research)
    monkeypatch.setattr(er, "GUIDE", research / "REPLICATION.md")
    problems = er.check()
    assert any("evaluate.py" in p and "not runnable" in p for p in problems), problems
