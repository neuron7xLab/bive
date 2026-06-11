from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Claim, EvidenceDirection, EvidenceEvent, Hypothesis


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: str
    label: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    weight: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class EvidenceGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    def structural_entropy(self) -> float:
        if not self.nodes:
            return 1.0
        edge_density = len(self.edges) / max(1, len(self.nodes) * (len(self.nodes) - 1))
        return round(max(0.0, min(1.0, 1.0 - edge_density)), 4)


def build_evidence_graph(
    claims: list[Claim], events: list[EvidenceEvent], hypotheses: list[Hypothesis]
) -> EvidenceGraph:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for claim in claims:
        nodes.append(GraphNode(claim.claim_id, "claim", claim.text[:96], claim.to_dict()))
    for event in events:
        nodes.append(GraphNode(event.event_id, "evidence", event.feature, event.to_dict()))
        for hid in event.hypothesis_refs:
            relation = (
                "supports"
                if event.direction == EvidenceDirection.SUPPORTS
                else "refutes"
                if event.direction == EvidenceDirection.REFUTES
                else "observes"
            )
            edges.append(
                GraphEdge(
                    event.event_id, hid, relation, round(event.confidence * event.magnitude, 4)
                )
            )
    for hyp in hypotheses:
        nodes.append(GraphNode(hyp.hypothesis_id, "hypothesis", hyp.label, hyp.to_dict()))
        for eid in hyp.evidence_for:
            edges.append(GraphEdge(eid, hyp.hypothesis_id, "supports", hyp.score))
        for eid in hyp.evidence_against:
            edges.append(GraphEdge(eid, hyp.hypothesis_id, "refutes", hyp.score))
    return EvidenceGraph(tuple(nodes), tuple(edges))
