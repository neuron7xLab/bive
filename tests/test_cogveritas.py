from __future__ import annotations

import pytest

from bive.cogveritas import (
    analyze,
    build_output,
    classify_claim_verifiability,
    contains_forbidden_judgment,
    segment_claims,
    segment_sentences,
)
from bive.cogveritas.calibration_metrics import bootstrap_ci, reliability_diagram
from bive.cogveritas.output_contract import ECE_THRESHOLD, COGVERITASOutput, ProvenanceNode
from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.verifiability_tagger import build_provenance_nodes, normalize_text


def _node() -> ProvenanceNode:
    return ProvenanceNode(claim_id="c0", text="x", verifiability="insufficient_context")


# --- tagger ---

def test_text_normalization() -> None:
    assert normalize_text("  a\n\n b   c ") == "a b c"


def test_sentence_segmentation() -> None:
    assert segment_sentences("I went to Chicago. It rained! Did you?") == [
        "I went to Chicago.",
        "It rained!",
        "Did you?",
    ]


def test_claim_segmentation_and_short_input() -> None:
    assert segment_claims("I stayed at the Hilton on March 3.")  # a real claim
    assert segment_claims("no") == []  # too short


def test_verifiability_feature_counts_direction() -> None:
    verifiable, _ = analyze("I paid $200 at the Hilton on Michigan Avenue on March 3 at 9pm.")
    opinion, _ = analyze("I think it was a wonderful and amazing and perfect experience overall.")
    assert verifiable.count_verifiable >= 1
    assert verifiable.named_entity_count >= 1
    assert verifiable.verifiability_ratio > opinion.verifiability_ratio


def test_empty_and_short_input_return_insufficient() -> None:
    f, claims = analyze("")
    assert claims == []
    assert f.count_verifiable == 0
    from bive.cogveritas.verifiability_tagger import Claim

    assert classify_claim_verifiability(Claim("c", "a b", ["a", "b"])) == "insufficient_context"


def test_provenance_node_per_claim() -> None:
    _, claims = analyze("I stayed at the Hilton. The room cost 200 dollars.")
    nodes = build_provenance_nodes(claims)
    assert len(nodes) == len(claims) >= 2
    assert all("claim_id" in n and "verifiability" in n for n in nodes)


def test_service_audit_trail_carries_entities() -> None:
    # The audit trail is provenance: an externally-checkable claim must expose the
    # entities a reviewer would corroborate, not just assert the claim exists.
    out = analyze_verifiability("I met John Smith at the Hilton in Chicago on March 3.")
    checkable = [n for n in out.audit_trail if n.verifiability == "externally_checkable"]
    assert checkable, "a concrete claim must be externally checkable"
    assert any(n.entities for n in checkable), "checkable nodes must carry their entities"


def test_spacy_fallback_is_deterministic() -> None:
    # Without the optional spaCy model, entity extraction is a deterministic proxy.
    a, _ = analyze("John visited Boston in 2021.")
    b, _ = analyze("John visited Boston in 2021.")
    assert a.to_dict() == b.to_dict()


# --- metrics ---

def test_reliability_diagram_10_bins() -> None:
    rd = reliability_diagram([0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8], bins=10)
    assert len(rd["bin_edges"]) == 11
    assert len(rd["mean_predicted"]) == 10
    assert sum(rd["count"]) == 4


def test_bootstrap_ci_fixed_random_state() -> None:
    labels = [0, 0, 1, 1, 0, 1, 0, 1]
    scores = [0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6]
    assert bootstrap_ci(labels, scores, n_boot=200) == bootstrap_ci(labels, scores, n_boot=200)


# --- output contract (the invariant) ---

def test_verdict_always_none() -> None:
    out = build_output("nominal", ["Corroborate the date with an external record."], [_node()])
    assert out.verdict is None
    with pytest.raises(ValueError):
        COGVERITASOutput(
            verifiability_gap="nominal",
            corroboration_questions=["q"],
            ordinal_flag="markers_nominal",
            audit_trail=[_node()],
            verdict="deceptive",  # type: ignore[arg-type]
        )


def test_no_forbidden_person_level_strings() -> None:
    assert contains_forbidden_judgment("the subject is a liar") == ["liar"]
    with pytest.raises(ValueError):
        build_output("elevated", ["this person is a liar"], [_node()])


def test_no_float_probability_when_ece_fails() -> None:
    # ECE above threshold -> probabilities disabled, ordinal flags only.
    out = build_output(
        "elevated", ["Check the receipt."], [_node()],
        calibrated_probability=0.7, calibration_ci=(0.6, 0.8), ece=ECE_THRESHOLD + 0.01,
    )
    assert out.calibrated_probability is None
    assert out.calibration_ci is None
    assert out.ordinal_flag == "markers_elevated"
    # ECE below threshold -> probabilities allowed.
    ok = build_output(
        "elevated", ["Check the receipt."], [_node()],
        calibrated_probability=0.7, calibration_ci=(0.6, 0.8), ece=0.02,
    )
    assert ok.calibrated_probability == 0.7
    assert ok.calibration_ece == 0.02  # the passing evidence rides with the probability


def test_probability_cannot_bypass_calibration_via_direct_construction() -> None:
    # The suppression invariant must hold at the TYPE boundary, not only in
    # build_output — constructing the class directly must reject an unproven probability.
    base = {
        "verifiability_gap": "nominal",
        "corroboration_questions": ["Corroborate with an external record."],
        "ordinal_flag": "markers_nominal",
        "audit_trail": [_node()],
    }
    # No calibration evidence at all.
    with pytest.raises(ValueError, match="calibration_ece"):
        COGVERITASOutput(**base, calibrated_probability=0.93, calibration_ci=(0.88, 0.97))
    # Evidence present but ECE above threshold -> still rejected.
    with pytest.raises(ValueError, match="demonstrated calibration"):
        COGVERITASOutput(
            **base, calibrated_probability=0.93, calibration_ci=(0.88, 0.97),
            calibration_ece=ECE_THRESHOLD + 0.01,
        )
    # Orphan evidence without a probability is rejected too.
    with pytest.raises(ValueError, match="calibration_ece requires"):
        COGVERITASOutput(**base, calibration_ece=0.02)
    # A genuinely calibrated probability (ece below threshold) is accepted.
    good = COGVERITASOutput(
        **base, calibrated_probability=0.93, calibration_ci=(0.88, 0.97), calibration_ece=0.02
    )
    assert good.calibrated_probability == 0.93


def test_corroboration_and_audit_mandatory() -> None:
    with pytest.raises(ValueError):
        build_output("nominal", [], [_node()])
    with pytest.raises(ValueError):
        build_output("nominal", ["q"], [])


# --- fail-closed gates ---

def test_gates_fail_closed_on_missing_artifacts(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import cogveritas_gates as g  # type: ignore[import-not-found]

    monkeypatch.setattr(g, "V", tmp_path / "verification")
    monkeypatch.setattr(g, "DS", tmp_path / "datasets")
    monkeypatch.setattr(g, "REQUIRED_ARTIFACTS", [tmp_path / "missing.json"])
    with pytest.raises(g.GateFail):
        g.gate_subject_independent_auc()
    with pytest.raises(g.GateFail):
        g.gate_calibration_ece()
    with pytest.raises(g.GateFail):
        g.gate_artifact_manifest()


def test_bias_gate_blocks_release_when_unavailable() -> None:
    from bive.cogveritas.bias_baseline import evaluate_bias_gate

    result = evaluate_bias_gate(0.7, None, None, sensitive_fields=[])
    assert result["release_blocked"] is True
