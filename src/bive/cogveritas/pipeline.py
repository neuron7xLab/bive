"""Analysis pipeline — an ordered registry of analyzers, composed once.

Each analyzer is a pure function ``AnalysisContext -> dict`` contributing a slice
of the output. The registry ``ANALYZERS`` *is* the pipeline definition: a single,
auditable, ordered list. Adding a capability is one analyzer plus one registry
entry — the orchestrator is never edited, and the no-verdict invariant stays
enforced in one place (``build_output`` + the output-contract validator).

The registry order does not affect the serialized output (pydantic serializes in
model field order), so the integrity fingerprint is independent of it — but the
order is kept stable and meaningful for readability.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .corroboration import corroboration_questions, unverifiable_notes, verifiability_gap
from .entities import extract_entities
from .interview import interview_questions
from .lang import detect_language
from .output_contract import (
    ConflictItem,
    CrossWitnessItem,
    EntityRef,
    InterviewQuestion,
    ProvenanceNode,
    SpeakerProfile,
    TimelineEntry,
    WorklistItem,
)
from .timeline import build_timeline, detect_conflicts
from .verifiability_tagger import Claim, classify_claim_verifiability, extract_named_entities
from .witness import analyze_by_speaker, cross_witness, distinct_speakers, speaker_profiles
from .worklist import corroboration_worklist

_VALID_STATUS = {"pending", "confirmed", "refuted"}


@dataclass(frozen=True)
class AnalysisContext:
    """Everything an analyzer needs, computed once per review."""

    text: str
    lang: str
    claims: list[Claim]
    speakers: list[str]
    statuses: Mapping[str, dict[str, str]]

    @property
    def multi_speaker(self) -> bool:
        return len(self.speakers) > 1


def build_context(text: str, statuses: Mapping[str, dict[str, str]] | None = None) -> AnalysisContext:
    """Parse once (speaker-aware, so claim text is the clean utterance) and share."""
    lang = detect_language(text)
    claims = analyze_by_speaker(text)
    return AnalysisContext(text, lang, claims, distinct_speakers(claims), statuses or {})


# --- analyzers: each contributes a slice of build_output kwargs ------------- #


def _verifiability(ctx: AnalysisContext) -> dict[str, Any]:
    return {
        "verifiability_gap": verifiability_gap(ctx.claims),
        "corroboration_questions": corroboration_questions(ctx.claims),
        "rm_criteria_flagged": unverifiable_notes(ctx.claims),
        "detected_language": ctx.lang,
    }


def _audit_trail(ctx: AnalysisContext) -> dict[str, Any]:
    nodes = [
        ProvenanceNode(
            claim_id=c.claim_id,
            text=c.text,
            verifiability=classify_claim_verifiability(c),  # type: ignore[arg-type]
            entities=extract_named_entities(c.text, None)[:12],
        )
        for c in ctx.claims
    ]
    if not nodes:
        # Nothing analysable — stay insufficient, never fabricate signal.
        nodes = [ProvenanceNode(claim_id="claim:none", text=ctx.text[:200], verifiability="insufficient_context")]
    return {"audit_trail": nodes}


def _worklist(ctx: AnalysisContext) -> dict[str, Any]:
    items = [WorklistItem(**item) for item in corroboration_worklist(ctx.claims)]  # type: ignore[arg-type]
    if ctx.statuses:
        items = [
            item.model_copy(
                update={
                    "status": s["status"] if s.get("status") in _VALID_STATUS else item.status,
                    "note": s.get("note", item.note),
                }
            )
            if (s := ctx.statuses.get(item.claim_id))
            else item
            for item in items
        ]
    return {"corroboration_worklist": items}


def _interview(ctx: AnalysisContext) -> dict[str, Any]:
    return {"interview_questions": [InterviewQuestion(**q) for q in interview_questions(ctx.claims)]}  # type: ignore[arg-type]


def _timeline(ctx: AnalysisContext) -> dict[str, Any]:
    return {"timeline": [TimelineEntry(**e) for e in build_timeline(ctx.claims)]}  # type: ignore[arg-type]


def _conflicts(ctx: AnalysisContext) -> dict[str, Any]:
    return {"conflicts": [ConflictItem(**c) for c in detect_conflicts(ctx.claims)]}  # type: ignore[arg-type]


def _entities(ctx: AnalysisContext) -> dict[str, Any]:
    return {"entities": [EntityRef(**e) for e in extract_entities(ctx.claims)]}  # type: ignore[arg-type]


def _witness(ctx: AnalysisContext) -> dict[str, Any]:
    # Cross-witness structure is only meaningful with more than one named speaker.
    if not ctx.multi_speaker:
        return {"witnesses": [], "speaker_profiles": [], "cross_witness": []}
    return {
        "witnesses": ctx.speakers,
        "speaker_profiles": [SpeakerProfile(**p) for p in speaker_profiles(ctx.claims)],  # type: ignore[arg-type]
        "cross_witness": [CrossWitnessItem(**c) for c in cross_witness(ctx.claims)],  # type: ignore[arg-type]
    }


Analyzer = Callable[[AnalysisContext], dict[str, Any]]

# The pipeline. Adding a phase appends one entry here (plus its analyzer above).
ANALYZERS: list[tuple[str, Analyzer]] = [
    ("verifiability", _verifiability),
    ("audit_trail", _audit_trail),
    ("worklist", _worklist),
    ("interview", _interview),
    ("timeline", _timeline),
    ("conflicts", _conflicts),
    ("entities", _entities),
    ("witness", _witness),
]


def run_pipeline(ctx: AnalysisContext) -> dict[str, Any]:
    """Compose every analyzer's contribution into build_output kwargs."""
    kwargs: dict[str, Any] = {}
    for _name, analyzer in ANALYZERS:
        kwargs.update(analyzer(ctx))
    return kwargs
