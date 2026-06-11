from bive.evidence_graph import build_evidence_graph
from bive.fusion import EvidenceFusionEngine
from bive.ingest import TranscriptSegment
from bive.linguistics import LinguisticAnalyzer, extract_claims


def test_evidence_graph_has_nodes_and_entropy():
    claims = extract_claims([TranscriptSegment("s", "Не треба перевіряти. Повір мені.")])
    _, events = LinguisticAnalyzer().analyze(claims)
    hypotheses = EvidenceFusionEngine().build_hypotheses(events)
    graph = build_evidence_graph(claims, events, hypotheses)
    assert graph.nodes
    assert 0 <= graph.structural_entropy() <= 1
