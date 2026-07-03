"""COGVERITAS live service — text in, fail-closed verifiability output out.

Pure Python (no numpy/scikit-learn): usable directly in the core API. Enforces
the no-verdict invariant and the Phase 0 rule that probabilities are disabled
(cross-domain calibration is not demonstrated), so the output is ordinal only.
"""

from __future__ import annotations

from .corroboration import corroboration_questions, unverifiable_notes, verifiability_gap
from .dossier import to_dossier_markdown
from .lang import detect_language
from .output_contract import (
    COGVERITASOutput,
    ConflictItem,
    CrossWitnessItem,
    ProvenanceNode,
    TimelineEntry,
    WorklistItem,
    build_output,
)
from .timeline import build_timeline, detect_conflicts
from .verifiability_tagger import analyze, classify_claim_verifiability, extract_named_entities
from .witness import analyze_by_speaker, cross_witness, distinct_speakers
from .worklist import corroboration_worklist


def analyze_verifiability(text: str) -> COGVERITASOutput:
    """Run the fail-closed verifiability review. ``verdict`` is always ``None``."""
    lang = detect_language(text)
    _, claims = analyze(text)
    nodes = [
        ProvenanceNode(
            claim_id=c.claim_id,
            text=c.text,
            verifiability=classify_claim_verifiability(c),  # type: ignore[arg-type]
            # Carry the entities that make each claim externally checkable — the
            # audit trail must show what a reviewer would corroborate, not just
            # that a claim exists.
            entities=extract_named_entities(c.text)[:12],
        )
        for c in claims
    ]
    if not nodes:
        # Nothing analysable — stay insufficient, never fabricate signal.
        nodes = [
            ProvenanceNode(
                claim_id="claim:none",
                text=text[:200],
                verifiability="insufficient_context",
            )
        ]
    worklist = [WorklistItem(**item) for item in corroboration_worklist(claims)]  # type: ignore[arg-type]
    timeline = [TimelineEntry(**entry) for entry in build_timeline(claims)]  # type: ignore[arg-type]
    conflicts = [ConflictItem(**c) for c in detect_conflicts(claims)]  # type: ignore[arg-type]
    # Cross-witness: only meaningful when the input names more than one speaker.
    speaker_claims = analyze_by_speaker(text)
    speakers = distinct_speakers(speaker_claims)
    cross = (
        [CrossWitnessItem(**c) for c in cross_witness(speaker_claims)]  # type: ignore[arg-type]
        if len(speakers) > 1
        else []
    )
    return build_output(
        verifiability_gap=verifiability_gap(claims),
        corroboration_questions=corroboration_questions(claims),
        audit_trail=nodes,
        rm_criteria_flagged=unverifiable_notes(claims),
        corroboration_worklist=worklist,
        timeline=timeline,
        conflicts=conflicts,
        witnesses=speakers if len(speakers) > 1 else [],
        cross_witness=cross,
        detected_language=lang,
        # ece omitted -> Phase 0 policy disables float probabilities (ordinal only).
    )


def to_public_dict(output: COGVERITASOutput) -> dict[str, object]:
    """API-facing dict. ``verdict`` is explicit ``None`` for auditability."""
    return output.model_dump()


def analyze_dossier_markdown(text: str) -> str:
    """Full verifiability review rendered as a printable analyst dossier."""
    output = analyze_verifiability(text)
    return to_dossier_markdown(output, output.detected_language)
