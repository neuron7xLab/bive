"""Cross-domain matrix gate — the TF-IDF contamination proof is MANDATORY.

The central contamination evidence (high in-domain -> chance cross-corpus) must not
be silently skippable by dropping the ceiling rows, and the audited file must not be
able to widen its own passing band. These lock those invariants.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cross_domain_matrix_check as cdm  # noqa: E402  (needs scripts/ on sys.path first)


def _base_cells() -> list[dict[str, object]]:
    # A minimal honest matrix: degradation cross-domain + the leakage collapse.
    return [
        {"model": "verbal-science", "regime": "in-domain", "roc_auc": 0.75},
        {"model": "verbal-science", "regime": "cross-corpus", "roc_auc": 0.61},
        {"model": "verbal-science", "regime": "cross-domain-high-stakes", "roc_auc": 0.548},
        {"model": "tf-idf-ceiling", "regime": "in-domain", "roc_auc": 0.9548},
        {"model": "tf-idf-ceiling", "regime": "cross-corpus", "roc_auc": 0.51},
    ]


def _run(tmp_path: Path, monkeypatch, matrix: dict[str, object]) -> list[str]:
    """Run check() against a synthetic matrix; RESULTS consistency is out of scope here."""
    root = tmp_path
    (root / "research" / "cogveritas").mkdir(parents=True)
    (root / "research" / "cogveritas" / "cross_domain_matrix.json").write_text(
        json.dumps(matrix), encoding="utf-8"
    )
    monkeypatch.setattr(cdm, "ROOT", root)
    monkeypatch.setattr(cdm, "MATRIX", root / "research" / "cogveritas" / "cross_domain_matrix.json")
    monkeypatch.setattr(cdm, "RESULTS", root / "research" / "cogveritas" / "phase0_results.json")
    _artifact, problems = cdm.check()
    return problems


def test_honest_matrix_passes(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    problems = _run(tmp_path, monkeypatch, {"chance_band": [0.45, 0.58], "cells": _base_cells()})
    assert problems == [], f"honest matrix should pass, got: {problems}"


def test_dropping_the_ceiling_cross_row_fails(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The contamination proof must not be silently skippable.
    cells = [c for c in _base_cells() if not (c["model"] == "tf-idf-ceiling" and "cross" in str(c["regime"]))]
    problems = _run(tmp_path, monkeypatch, {"chance_band": [0.45, 0.58], "cells": cells})
    assert any("contamination proof absent" in p for p in problems), problems


def test_dropping_the_entire_ceiling_model_fails(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    cells = [c for c in _base_cells() if c["model"] != "tf-idf-ceiling"]
    problems = _run(tmp_path, monkeypatch, {"chance_band": [0.45, 0.58], "cells": cells})
    assert any("contamination proof absent" in p for p in problems), problems


def test_low_in_domain_ceiling_is_not_a_collapse(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # chance -> chance proves nothing; the in-domain leakage must be genuinely high.
    cells = _base_cells()
    for c in cells:
        if c["model"] == "tf-idf-ceiling" and c["regime"] == "in-domain":
            c["roc_auc"] = 0.55
    problems = _run(tmp_path, monkeypatch, {"chance_band": [0.45, 0.58], "cells": cells})
    assert any("below leakage floor" in p for p in problems), problems


def test_widened_chance_band_is_rejected(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The audited file cannot widen its own passing band to force a collapse verdict.
    problems = _run(tmp_path, monkeypatch, {"chance_band": [0.10, 0.90], "cells": _base_cells()})
    assert any("outside pinned envelope" in p for p in problems), problems


def test_ceiling_not_collapsing_fails(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    cells = _base_cells()
    for c in cells:
        if c["model"] == "tf-idf-ceiling" and "cross" in str(c["regime"]):
            c["roc_auc"] = 0.80  # stays high cross-corpus -> not a collapse
    problems = _run(tmp_path, monkeypatch, {"chance_band": [0.45, 0.58], "cells": cells})
    assert any("does not collapse" in p for p in problems), problems


def test_the_frozen_repo_matrix_still_passes() -> None:
    # Guard against the pinned thresholds diverging from the real frozen artifact.
    _artifact, problems = cdm.check()
    assert problems == [], f"frozen repo matrix must still pass the hardened gate: {problems}"
