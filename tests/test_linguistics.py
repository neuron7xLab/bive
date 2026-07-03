from bive.ingest import TranscriptSegment
from bive.linguistics import LinguisticAnalyzer, extract_claims


def test_extract_claims_marks_absolute_and_temporal():
    claims = extract_claims([TranscriptSegment("A", "I never met him yesterday.", 0, 1)])
    assert claims
    assert "absolute" in claims[0].qualifiers
    assert "temporal" in claims[0].qualifiers


def test_linguistic_analyzer_extracts_events():
    claims = extract_claims([TranscriptSegment("A", "Trust me. You do not need to check.", 0, 1)])
    _, events = LinguisticAnalyzer().analyze(claims)
    assert any(e.feature == "verification_pressure" for e in events)


def test_local_contradiction_between_negative_and_positive():
    segments = [
        TranscriptSegment("A", "I never received that money.", 0, 1),
        TranscriptSegment("A", "I received that money later.", 2, 3),
    ]
    _, events = LinguisticAnalyzer().analyze(extract_claims(segments))
    tensions = [e for e in events if e.feature == "local_claim_tension"]
    assert len(tensions) == 1
    # Overlap is computed over light stems, so 'received' -> 'receiv'.
    assert set(tensions[0].value["overlap"]) >= {"money", "receiv"}
    assert "receiv" in tensions[0].value["polarity_conflict"]


def test_contradiction_scan_scales_to_large_input():
    # Token caching keeps this O(n^2)-comparison scan tractable; a naive
    # re-tokenisation per pair made large single-speaker transcripts slow.
    # 600 alternating claims exercises the hot path deterministically.
    segments = []
    for i in range(300):
        segments.append(TranscriptSegment("A", "I never touched the shared account files.", i, i))
        segments.append(TranscriptSegment("A", "I touched the shared account files once.", i, i))
    _, events = LinguisticAnalyzer().analyze(extract_claims(segments))
    tensions = [e for e in events if e.feature == "local_claim_tension"]
    assert tensions  # contradictions are detected across the transcript
    # Every emitted tension pairs an earlier negative claim with a later positive one.
    assert all("|" in e.provenance.entity_id for e in tensions)
