from __future__ import annotations

from bive.ingest import TranscriptSegment
from bive.linguistics import _content_and_negated, _stem, extract_claims
from bive.models import EvidenceDirection
from bive.report import build_report_from_segments
from bive.style_markers import build_style_events, compute_markers


def _tension_count(segments: list[TranscriptSegment]) -> int:
    report = build_report_from_segments(segments)
    return len([e for e in report.evidence_events if e.feature == "local_claim_tension"])


def test_short_text_yields_no_markers() -> None:
    assert compute_markers("too short to analyse") == []


def test_impression_management_marker_fires() -> None:
    text = " ".join(
        ["Believe me, to tell the truth I am proud and honest."] * 20
    )
    features = {hit.feature for hit in compute_markers(text)}
    assert "impression_management" in features


def test_high_verifiability_is_counter_evidence() -> None:
    # Dense checkable detail (names, numbers) is exculpatory under the
    # Verifiability Approach — a REFUTES-direction event.
    text = (
        "On March 3 2021 in Boston, John Smith paid $18,000 to Acme Corp; "
        "invoice 4471 was audited by Price Waterhouse for $41,000 and $3,500. "
    ) * 6
    hits = {hit.feature: hit for hit in compute_markers(text)}
    assert "high_verifiability" in hits
    assert hits["high_verifiability"].direction == EvidenceDirection.REFUTES


def test_style_events_carry_citations() -> None:
    claims = extract_claims(
        [TranscriptSegment("s", "Believe me, honestly, to tell the truth, I am proud. " * 20)]
    )
    events = build_style_events(claims)
    assert events
    refs = {e.provenance.parameters.get("reference") for e in events}
    assert refs & {"newman_pennebaker_2003", "vrij_2008", "ekman_friesen_1969"}
    for event in events:
        assert event.limitations  # every marker is paired with a limitation


def test_stemmer_aligns_inflections() -> None:
    assert _stem("received") == _stem("receive")
    assert _stem("charged") == _stem("charge")


def test_negation_scope_marks_negated_content() -> None:
    content, negated = _content_and_negated("i did not receive that money")
    assert "receiv" in content
    assert "receiv" in negated


def test_contradiction_requires_polarity_and_overlap() -> None:
    # Genuine opposition on shared content.
    assert _tension_count(
        [
            TranscriptSegment("s", "I never received that money.", 0, 1),
            TranscriptSegment("s", "I received that money later.", 2, 3),
        ]
    ) == 1
    # Shared polysemous verb but different topics — not a tension.
    assert _tension_count(
        [
            TranscriptSegment("s", "I believe we have had enough of that today.", 0, 1),
            TranscriptSegment("s", "I do not believe in raising the tariff schedule.", 2, 3),
        ]
    ) == 0


def test_style_hypothesis_present_in_report() -> None:
    text = " ".join(["Believe me, I am proud, honest and here to tell the truth."] * 30)
    report = build_report_from_segments([TranscriptSegment("s", text)])
    labels = {h.label for h in report.hypotheses}
    assert "linguistic_style_risk" in labels
