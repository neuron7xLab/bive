"""PR-7 Capability Registry — declared capabilities must be backed by code."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import capability_registry_check as cr  # noqa: E402  (needs scripts/ on sys.path first)


def test_registry_live_passes() -> None:
    _artifact, problems = cr.check()
    assert problems == []


def test_every_capability_is_backed_by_a_real_module() -> None:
    artifact, _ = cr.check()
    caps = artifact["capabilities"]
    assert caps
    for cap in caps:  # type: ignore[union-attr]
        assert cap["backed"] is True, f"unbacked capability: {cap['id']}"
        assert (cr.ROOT / str(cap["backing"])).is_file()


def test_gate_emits_artifact_with_human_in_the_loop() -> None:
    assert cr.main() == 0
    art = json.loads(cr.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert art["human_in_the_loop"] is True
    assert art["capability_count"] >= 10


def test_unbacked_capability_would_fail(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # If a declared capability had no backing entry, the gate must flag it.
    original = dict(cr._BACKING)
    monkeypatch.setattr(cr, "_BACKING", {**original, "verifiability": "src/bive/cogveritas/DOES_NOT_EXIST.py"})
    _artifact, problems = cr.check()
    assert any("backing module missing" in p for p in problems)


# --- existence is not backing: a stub module must fail ---


def test_stub_backing_module_is_not_backed(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # A capability whose backing module is a NotImplementedError stub must NOT be
    # reported as backed (file existence is not backing code).
    stub = tmp_path / "stub_mod.py"
    stub.write_text(
        "def a():\n    raise NotImplementedError\n\ndef b():\n    pass\n\ndef c():\n    ...\n", encoding="utf-8"
    )
    original = dict(cr._BACKING)
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    monkeypatch.setattr(cr, "_BACKING", {**original, "verifiability": "stub_mod.py"})
    artifact, problems = cr.check()
    assert any("verifiability" in p and "not a real implementation" in p for p in problems), problems
    verif = next(c for c in artifact["capabilities"] if c["id"] == "verifiability")  # type: ignore[union-attr]
    assert verif["backed"] is False


def test_real_module_is_not_flagged_as_stub() -> None:
    for backing in set(cr._BACKING.values()):
        src = (cr.ROOT / backing).read_text(encoding="utf-8")
        assert cr._module_stub_reason(src) is None, f"{backing} misclassified as stub"


def test_stub_reason_detects_placeholders() -> None:
    assert cr._module_stub_reason("") is not None
    assert cr._module_stub_reason("# only a comment\n") is not None
    all_stub = "import os\ndef x():\n    raise NotImplementedError\ndef y():\n    pass\ndef z():\n    ...\nA=1\nB=2\n"
    assert cr._module_stub_reason(all_stub) == "every function is a stub (pass/.../NotImplementedError)"
