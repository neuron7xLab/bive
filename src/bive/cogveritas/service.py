"""COGVERITAS live service — text in, fail-closed verifiability output out.

Pure Python (no numpy/scikit-learn): usable directly in the core API. Enforces
the no-verdict invariant and the Phase 0 rule that probabilities are disabled
(cross-domain calibration is not demonstrated), so the output is ordinal only.
"""

from __future__ import annotations

from .corroboration import corroboration_questions, unverifiable_notes, verifiability_gap
from .output_contract import COGVERITASOutput, ProvenanceNode, build_output
from .verifiability_tagger import analyze, classify_claim_verifiability, extract_named_entities


def analyze_verifiability(text: str) -> COGVERITASOutput:
    """Run the fail-closed verifiability review. ``verdict`` is always ``None``."""
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
    return build_output(
        verifiability_gap=verifiability_gap(claims),
        corroboration_questions=corroboration_questions(claims),
        audit_trail=nodes,
        rm_criteria_flagged=unverifiable_notes(claims),
        # ece omitted -> Phase 0 policy disables float probabilities (ordinal only).
    )


def to_public_dict(output: COGVERITASOutput) -> dict[str, object]:
    """API-facing dict. ``verdict`` is explicit ``None`` for auditability."""
    return output.model_dump()
