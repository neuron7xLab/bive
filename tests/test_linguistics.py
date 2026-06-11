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
