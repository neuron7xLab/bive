import pytest

from bive.models import EvidenceDirection, EvidenceEvent, Modality


def test_evidence_event_bounds():
    with pytest.raises(ValueError):
        EvidenceEvent("e", "s", Modality.TEXT, "f", "v", 1.2)


def test_weighted_score_supports_and_refutes():
    support = EvidenceEvent(
        "e1", "s", Modality.TEXT, "f", "v", 0.5, EvidenceDirection.SUPPORTS, 0.5
    )
    refute = EvidenceEvent("e2", "s", Modality.TEXT, "f", "v", 0.5, EvidenceDirection.REFUTES, 0.5)
    assert support.weighted_score() == 0.25
    assert refute.weighted_score() == -0.25
