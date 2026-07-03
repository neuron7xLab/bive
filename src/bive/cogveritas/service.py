"""COGVERITAS live service — text in, fail-closed verifiability output out.

Pure Python (no numpy/scikit-learn): usable directly in the core API. Enforces
the no-verdict invariant and the Phase 0 rule that probabilities are disabled
(cross-domain calibration is not demonstrated), so the output is ordinal only.
"""

from __future__ import annotations

from .dossier import to_dossier_markdown
from .integrity import compute_integrity
from .output_contract import COGVERITASOutput, IntegrityBlock, build_output
from .pipeline import build_context, run_pipeline


def analyze_verifiability(
    text: str, statuses: dict[str, dict[str, str]] | None = None
) -> COGVERITASOutput:
    """Run the fail-closed verifiability review. ``verdict`` is always ``None``.

    Thin orchestrator: build the analysis context once, run the analyzer pipeline
    (see ``pipeline.ANALYZERS``), assemble the typed output, and stamp a
    deterministic integrity fingerprint. New capabilities are added as pipeline
    analyzers, not by editing this function.

    ``statuses`` is an optional analyst overlay keyed by ``claim_id`` — each entry
    may carry a corroboration ``status`` (pending/confirmed/refuted) and a ``note``,
    recording a *human's* finding against external records. The system never sets
    these itself; it only echoes them and tallies verification progress.
    """
    ctx = build_context(text, statuses)
    output = build_output(**run_pipeline(ctx))
    # Stamp a deterministic chain-of-custody fingerprint over source + analysis.
    block = compute_integrity(text, output.model_dump())
    return output.model_copy(update={"integrity": IntegrityBlock(**block)})


def to_public_dict(output: COGVERITASOutput) -> dict[str, object]:
    """API-facing dict. ``verdict`` is explicit ``None`` for auditability."""
    return output.model_dump()


def analyze_dossier_markdown(text: str, statuses: dict[str, dict[str, str]] | None = None) -> str:
    """Full verifiability review rendered as a printable analyst dossier."""
    output = analyze_verifiability(text, statuses)
    return to_dossier_markdown(output, output.detected_language)


def verify_integrity(
    text: str,
    expected: dict[str, str],
    statuses: dict[str, dict[str, str]] | None = None,
) -> dict[str, object]:
    """Recompute the fingerprint from ``text`` and compare to ``expected``.

    Reproducibility check for chain-of-custody: only the fields present in
    ``expected`` are compared; ``match`` is True iff every provided field agrees
    with the freshly computed fingerprint.
    """
    recomputed = analyze_verifiability(text, statuses).integrity
    fields = ("engine", "source_sha256", "analysis_sha256", "case_id")
    mismatches = [
        f for f in fields if f in expected and expected[f] != getattr(recomputed, f)
    ]
    return {
        "match": not mismatches,
        "mismatched_fields": mismatches,
        "integrity": recomputed.model_dump(),
    }
