"""PR-1 gates — Benchmark Card + Contamination Audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import benchmark_card as bc  # noqa: E402  (needs scripts/ on sys.path first)
import contamination_audit as ca  # noqa: E402


def test_benchmark_card_live_is_consistent() -> None:
    assert bc.check() == []


def test_contamination_audit_live_is_clean() -> None:
    assert ca.audit() == []


def test_benchmark_gate_emits_machine_readable_artifact() -> None:
    assert bc.main() == 0
    art = json.loads(bc.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert art["benchmarks"] and art["benchmarks"][0]["results"]
    # A high headline must carry the contamination flag; the calibrated model must not.
    flags = {r["model"]: r["contamination_flag"] for r in art["benchmarks"][0]["results"]}
    assert any(v for v in flags.values()), "no contamination-flagged ceiling row"


def test_contamination_gate_emits_artifact_with_threshold() -> None:
    assert ca.main() == 0
    art = json.loads(ca.OUT.read_text(encoding="utf-8"))
    assert art["status"] == "PASS"
    assert art["leakage_threshold"] == 0.85
    assert art["violations"] == []


def test_contamination_bites_on_unqualified_high_auc() -> None:
    # A bare high headline with no leakage/cross-corpus framing must be flagged.
    assert ca.unqualified_high_auc("Our model achieves 0.95 AUC on the benchmark.")


def test_contamination_allows_qualified_high_auc() -> None:
    text = "The TF-IDF ceiling reaches 0.95 AUC but collapses cross-corpus to 0.51 (leakage)."
    assert ca.unqualified_high_auc(text) == []


def test_contamination_ignores_low_auc() -> None:
    assert ca.unqualified_high_auc("The interpretable model holds 0.61 out of domain.") == []


# --- headline consistency must be mandatory and bidirectional ---

_VALID_CARD = (
    "Size: 100\n"
    "Split: train/test disjoint\n"
    "Provenance: public\n"
    "Limitation: chance on real high-stakes\n"
    "Contamination controls: cross-corpus leakage audit\n"
    "Real-Life Trial (RLT) cross-corpus regime\n"
    "verbal-science AUC 0.7507\n"
)
_VALID_RESULTS = {
    "corpus": "synthetic",
    "protocol": "nested CV",
    "limitation": "chance on real",
    "results": [
        {"model": "verbal-science (calibrated)", "roc_auc": 0.7507, "ece": 0.02},
        {"model": "baseline: length-only", "roc_auc": 0.50},
    ],
}


def _run_card(tmp_path: Path, monkeypatch, card_text: str, results: dict[str, object]) -> list[str]:
    card_p = tmp_path / "CARD.md"
    res_p = tmp_path / "results.json"
    card_p.write_text(card_text, encoding="utf-8")
    res_p.write_text(json.dumps(results), encoding="utf-8")
    monkeypatch.setattr(bc, "CARD", card_p)
    monkeypatch.setattr(bc, "RESULTS", res_p)
    monkeypatch.setattr(bc, "MATRIX", tmp_path / "no_matrix.json")  # isolate to results + constants
    return bc.check()


def test_valid_minimal_card_passes(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    assert _run_card(tmp_path, monkeypatch, _VALID_CARD, _VALID_RESULTS) == []


def test_missing_headline_entry_fails(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Renaming the verbal-science result away must NOT silently skip the proof.
    res = json.loads(json.dumps(_VALID_RESULTS))
    res["results"][0]["model"] = "renamed-away"
    problems = _run_card(tmp_path, monkeypatch, _VALID_CARD, res)
    assert any("missing the headline verbal-science entry" in p for p in problems), problems


def test_card_auc_absent_from_artifacts_fails(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The reverse direction: a headline number the artifact does not contain.
    card = _VALID_CARD + "novel-model AUC 0.88 on the held-out set\n"
    problems = _run_card(tmp_path, monkeypatch, card, _VALID_RESULTS)
    assert any("0.88 absent from the frozen artifacts" in p for p in problems), problems


def test_ci_bounds_and_ece_are_not_flagged(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # CI intervals and ECE are legitimate and must not be mistaken for AUC claims.
    card = _VALID_CARD.replace(
        "verbal-science AUC 0.7507\n",
        "verbal-science AUC 0.7507 [0.7269-0.7742], ECE 0.0239\n",
    )
    assert _run_card(tmp_path, monkeypatch, card, _VALID_RESULTS) == []


def test_live_card_auc_claims_all_supported() -> None:
    card = bc.CARD.read_text(encoding="utf-8")
    data = json.loads(bc.RESULTS.read_text(encoding="utf-8"))
    allowed = bc._allowed_auc_strings(data)
    unsupported = [c for c in bc._card_auc_claims(card) if c not in allowed]
    assert unsupported == [], unsupported
