from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from .evidence_graph import build_evidence_graph
from .fusion import EvidenceFusionEngine
from .ingest import TranscriptSegment, load_transcript
from .linguistics import LinguisticAnalyzer, extract_claims
from .models import (
    EvidenceEvent,
    Hypothesis,
    ProvenanceRecord,
    ReviewStatus,
    VerificationReport,
    utc_now_iso,
)
from .questions import build_verification_questions

DEFAULT_LIMITATIONS = (
    "This report is not a lie detector and must not be used as an automated accusation.",
    "Nonverbal and paralinguistic cues are weak without baseline, context, and corroborating evidence.",
    "Text-only analysis cannot infer physiology, identity, intent, or guilt.",
    "Real-world use requires human review, source provenance, and domain-specific validation.",
)


def build_report_from_segments(
    segments: list[TranscriptSegment], subject_scope: str = "single_session"
) -> VerificationReport:
    claims = extract_claims(segments)
    signals, events = LinguisticAnalyzer().analyze(claims)
    hypotheses = EvidenceFusionEngine().build_hypotheses(events)
    final_status = EvidenceFusionEngine().final_status(hypotheses)
    graph = build_evidence_graph(claims, events, hypotheses)
    missing = build_missing_evidence(events)
    assessment = build_final_assessment(
        final_status, hypotheses, len(claims), len(events), graph.structural_entropy()
    )
    provenance = (
        ProvenanceRecord(
            entity_id="report",
            activity="verification_report_generation",
            agent="bive.report.build_report_from_segments",
            source="transcript_segments",
            parameters={"segment_count": len(segments), "claim_count": len(claims)},
        ),
    )
    return VerificationReport(
        report_id="bive-report-0001",
        created_at=utc_now_iso(),
        subject_scope=subject_scope,
        input_summary={
            "segments": len(segments),
            "claims": len(claims),
            "modalities": ["text"],
            "evidence_graph_entropy": graph.structural_entropy(),
            "graph_nodes": len(graph.nodes),
            "graph_edges": len(graph.edges),
        },
        claims=tuple(claims),
        signals=tuple(signals),
        evidence_events=tuple(events),
        hypotheses=tuple(hypotheses),
        final_status=final_status,
        final_assessment=assessment,
        limitations=DEFAULT_LIMITATIONS,
        missing_evidence=missing,
        verification_questions=build_verification_questions(claims, hypotheses),
        provenance=provenance,
    )


def build_report_from_transcript(path: str | Path) -> VerificationReport:
    return build_report_from_segments(load_transcript(path))


def build_missing_evidence(events: Sequence[EvidenceEvent]) -> tuple[str, ...]:
    missing = [
        "speaker baseline across neutral conditions",
        "external factual timeline",
        "raw audio/video quality metrics",
        "independent corroborating documents",
    ]
    if not events:
        missing.append("extractable evidence events")
    return tuple(missing)


def build_final_assessment(
    status: ReviewStatus,
    hypotheses: Sequence[Hypothesis],
    claim_count: int,
    event_count: int,
    graph_entropy: float = 1.0,
) -> str:
    top = sorted(hypotheses, key=lambda h: h.score, reverse=True)[:2]
    top_text = ", ".join(f"{h.label}={h.score:.2f}/u={h.uncertainty:.2f}" for h in top)
    return (
        f"Status: {status.value}. The system extracted {claim_count} claims and {event_count} evidence events. "
        f"Top hypotheses: {top_text or 'none'}. Evidence graph entropy={graph_entropy:.2f}. "
        f"This is a review surface, not a person-level verdict."
    )


def save_report(report: VerificationReport, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_report(path: str | Path) -> VerificationReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return VerificationReport.from_dict(data)


def render_markdown(report: VerificationReport) -> str:
    lines = [
        f"# BIVE Verification Report `{report.report_id}`",
        "",
        f"Created: {report.created_at}",
        f"Final status: **{report.final_status.value}**",
        "",
        "## Assessment",
        report.final_assessment,
        "",
        "## Hypotheses",
    ]
    for h in report.hypotheses:
        lines.extend(
            [
                f"### {h.label}",
                f"- score: `{h.score}`",
                f"- uncertainty: `{h.uncertainty}`",
                f"- status: `{h.status.value}`",
                f"- evidence_for: `{len(h.evidence_for)}`",
                f"- evidence_against: `{len(h.evidence_against)}`",
                f"- alternatives: {', '.join(h.alternative_explanations) if h.alternative_explanations else 'none'}",
                "",
            ]
        )
    lines.extend(["## Verification questions"])
    for q in report.verification_questions:
        lines.append(f"- {q}")
    lines.extend(["", "## Limitations"])
    for lim in report.limitations:
        lines.append(f"- {lim}")
    return "\n".join(lines) + "\n"
