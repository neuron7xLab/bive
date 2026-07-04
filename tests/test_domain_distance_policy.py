"""PR-2 Cross-Domain Matrix + Domain-Distance Policy gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cross_domain_matrix_check as cd  # noqa: E402  (needs scripts/ on sys.path first)
import domain_distance_check as dd  # noqa: E402


def test_cross_domain_matrix_live_passes() -> None:
    artifact, problems = cd.check()
    assert problems == []
    assert artifact["status"] == "PASS"


def test_cross_domain_gate_emits_artifact_with_degradation() -> None:
    assert cd.main() == 0
    art = json.loads(cd.OUT.read_text(encoding="utf-8"))
    # in-domain cell must be present and cross-domain cells must not exceed it.
    vs = [c for c in art["cells"] if c["model"] == "verbal-science"]
    in_domain = next(c for c in vs if c["regime"] == "in-domain")
    for c in vs:
        if "cross" in c["regime"]:
            assert c["roc_auc"] <= in_domain["roc_auc"]


def test_tfidf_ceiling_collapses_toward_chance() -> None:
    art, _ = cd.check()
    tf = [c for c in art["cells"] if c["model"] == "tf-idf-ceiling"]  # type: ignore[union-attr]
    in_d = next(c for c in tf if c["regime"] == "in-domain")
    cross = next(c for c in tf if "cross" in c["regime"])
    assert in_d["roc_auc"] >= 0.85  # a high, contaminated headline
    assert cross["roc_auc"] <= 0.58  # collapses to chance cross-corpus


def test_domain_distance_live_passes_and_suppresses_probability() -> None:
    assert dd.check() == []
    assert dd._probability_suppressed_at_runtime() is True


def test_domain_distance_gate_emits_policy_artifact() -> None:
    assert dd.main() == 0
    art = json.loads(dd.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert art["runtime_probability_suppressed"] is True
    regimes = {r["regime"] for r in art["policy"]}
    assert "in-domain" in regimes and "unknown" in regimes
