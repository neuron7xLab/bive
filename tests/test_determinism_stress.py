"""Determinism stress and regression guards.

These lock in the two latent non-determinism defects that previously made the
release gate flaky on a fresh checkout:

1. the dynamic-probe "structural" hash drifted whenever the wall clock ticked,
   because nested ``provenance.generated_at`` timestamps were not normalized;
2. ``VERIFY_RELEASE.log`` (random pip temp paths + per-build wheel sha256) was
   pinned in the artifact manifest, which can never be byte-stable.

The tests are intentionally adversarial: they try to make the hash move and
assert it does not, and they try to flip substantive content and assert it
does.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_VOLATILE_KEYS = {"report_id", "created_at", "generated_at", "timestamp"}


def _load_probe() -> Any:
    spec = importlib.util.spec_from_file_location(
        "dynamic_environment_probe", ROOT / "scripts" / "dynamic_environment_probe.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = _load_probe()


def _report(text: str = "the audited claim about the timeline") -> dict[str, Any]:
    from bive.pipeline import analyze_transcript_payload

    payload = {"segments": [{"speaker": "subject", "text": text}]}
    return analyze_transcript_payload(payload).to_dict()


def _rewrite_volatile(value: Any, stamp: str) -> Any:
    if isinstance(value, dict):
        return {
            key: stamp if key in _VOLATILE_KEYS else _rewrite_volatile(item, stamp)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_rewrite_volatile(item, stamp) for item in value]
    return value


def test_structural_hash_invariant_to_wall_clock() -> None:
    """Defect 1 guard: any timestamp value, at any depth, must hash identically."""
    report = _report()
    base = probe._stable_hash(report)
    for stamp in (
        "1970-01-01T00:00:01Z",
        "2026-06-11T11:16:03Z",
        "2026-06-11T11:16:04Z",  # the one-second neighbour that used to flip the hash
        "2099-12-31T23:59:59Z",
    ):
        mutated = _rewrite_volatile(copy.deepcopy(report), stamp)
        assert probe._stable_hash(mutated) == base, f"structural hash drifted for stamp {stamp}"


def test_structural_hash_stable_over_many_builds() -> None:
    """Stress: rebuilding the same report many times yields exactly one hash."""
    hashes = {probe._stable_hash(_report()) for _ in range(64)}
    assert len(hashes) == 1, f"non-deterministic structural hash across rebuilds: {hashes}"


def test_normalizer_preserves_substantive_content() -> None:
    """Sensitivity guard: the normalizer must not blank real, distinguishing content."""
    assert probe._stable_hash(_report("alpha")) != probe._stable_hash(_report("omega"))


def test_normalizer_blanks_only_volatile_keys() -> None:
    """A substantive field change must move the hash even after normalization."""
    report = _report()
    base = probe._stable_hash(report)
    mutated = copy.deepcopy(report)
    mutated["subject_scope"] = f"{mutated['subject_scope']}-perturbed"
    assert probe._stable_hash(mutated) != base


def test_manifest_excludes_nonreproducible_log() -> None:
    """Defect 2 guard: the volatile run log must never be pinned in the manifest."""
    manifest = json.loads((ROOT / "ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    pinned = {entry["path"] for entry in manifest["files"]}
    assert "artifacts/verification/VERIFY_RELEASE.log" not in pinned


def test_volatile_log_is_gitignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "artifacts/verification/VERIFY_RELEASE.log" in gitignore
