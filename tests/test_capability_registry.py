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
