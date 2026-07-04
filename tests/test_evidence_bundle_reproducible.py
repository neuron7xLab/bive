"""The committed evidence bundle must be a pure function of the commit.

gates.json and EVIDENCE_BUNDLE.json are tracked. If regenerating them changes a
single byte, the working tree goes dirty on every ``make verify-release`` /
``make institutional-verify`` run — and, worse, the maturity claim rests on numbers
(durations, timestamps) that cannot be reproduced from the commit. This is the
falsifier: reintroduce any wall-clock / self-referential field into the committed
payload and this test fails.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_script(relative: str) -> ModuleType:
    path = Path(relative)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


_TRACKED = (
    Path("artifacts/verification/gates.json"),
    Path("artifacts/verification/EVIDENCE_BUNDLE.json"),
)


def _regenerate_prerequisites() -> None:
    assert _load_script("scripts/validate_dependency_contracts.py").main() == 0
    assert _load_script("scripts/validate_test_architecture.py").main() == 0
    assert _load_script("scripts/validate_automation_contract.py").main() == 0
    assert _load_script("scripts/validate_bibliography.py").main() == 0
    if not Path("artifacts/verification/DYNAMIC_ENVIRONMENT_PROBE.json").exists():
        assert _load_script("scripts/dynamic_environment_probe.py").main() == 0


@pytest.mark.slow
def test_evidence_bundle_regeneration_is_byte_stable() -> None:
    """Two consecutive regenerations produce byte-identical tracked artifacts."""
    evidence_main = _load_script("scripts/generate_evidence_bundle.py").main
    _regenerate_prerequisites()

    assert evidence_main() == 0
    first = {path: path.read_bytes() for path in _TRACKED}
    assert evidence_main() == 0
    second = {path: path.read_bytes() for path in _TRACKED}

    for path in _TRACKED:
        assert first[path] == second[path], f"{path} is non-deterministic across regenerations"


@pytest.mark.slow
def test_volatile_audit_output_does_not_perturb_the_bundle() -> None:
    """Mutating a witnessed volatile artifact (pip-audit.json — a live CVE snapshot)
    must NOT change the committed bundle. This is the exact regression that made the
    CI capstone fail: the bundle pinned pip-audit.json's sha256, so every dependency
    audit (fresh vuln DB, new timestamp) dirtied the evidence."""
    import json

    audit = Path("artifacts/security/pip-audit.json")
    evidence_main = _load_script("scripts/generate_evidence_bundle.py").main
    _regenerate_prerequisites()

    assert evidence_main() == 0
    before = _TRACKED[1].read_bytes()
    bundle = json.loads(_TRACKED[1].read_text())
    witnessed = [e for e in bundle["entries"] if e["path"] == audit.as_posix()]
    assert witnessed and witnessed[0].get("volatile") is True, "pip-audit.json must be witnessed, not pinned"
    assert "sha256" not in witnessed[0], "witnessed entry must not pin a hash"

    original = audit.read_bytes()
    try:
        audit.write_text(audit.read_text() + "\n// volatile drift\n")
        assert evidence_main() == 0
        assert _TRACKED[1].read_bytes() == before, "volatile audit drift leaked into the bundle"
    finally:
        audit.write_bytes(original)
        evidence_main()


@pytest.mark.slow
def test_evidence_bundle_carries_no_wall_clock_fields() -> None:
    """The committed payload must not embed timing/timestamp/commit — those are
    volatile and belong in the gitignored telemetry sink, not the evidence."""
    import json

    evidence_main = _load_script("scripts/generate_evidence_bundle.py").main
    _regenerate_prerequisites()
    assert evidence_main() == 0

    gates = json.loads(_TRACKED[0].read_text())
    bundle = json.loads(_TRACKED[1].read_text())
    for forbidden in ("generated_at", "commit"):
        assert forbidden not in gates, f"gates.json leaks volatile field {forbidden!r}"
        assert forbidden not in bundle, f"EVIDENCE_BUNDLE.json leaks volatile field {forbidden!r}"
    for gate in gates["gates"]:
        assert "duration_seconds" not in gate, "gates.json leaks wall-clock duration_seconds"
