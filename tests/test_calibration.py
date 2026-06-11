from bive.calibration import calibrate_hypothesis
from bive.models import EvidenceDirection, EvidenceEvent, Modality


def test_single_modality_caps_overconfidence():
    events = [
        EvidenceEvent(
            event_id=f"e{i}",
            source_id="s",
            modality=Modality.TEXT,
            feature="f",
            value="v",
            confidence=0.95,
            magnitude=0.95,
            direction=EvidenceDirection.SUPPORTS,
            hypothesis_refs=("H_INCONSISTENCY_RISK",),
        )
        for i in range(6)
    ]
    result = calibrate_hypothesis(0.5, events)
    assert result.score <= 0.66
    assert "single modality penalty applied" in result.notes


def test_counterevidence_increases_calm():
    support = EvidenceEvent(
        "s", "src", Modality.TEXT, "pressure", "x", 0.8, EvidenceDirection.SUPPORTS, 0.8
    )
    refute = EvidenceEvent(
        "r",
        "src",
        Modality.CONTEXT,
        "document_check",
        "verified",
        0.9,
        EvidenceDirection.REFUTES,
        0.8,
    )
    only_support = calibrate_hypothesis(0.5, [support])
    with_refute = calibrate_hypothesis(0.5, [support, refute])
    assert with_refute.score < only_support.score
