"""COGVERITAS capability envelope — what the tool does, and what it never does.

A machine-readable, honest statement of the operational surface: the analyst
capabilities that exist, and the hard limits that are structurally enforced. Kept
separate from the methodology contract (which explains *why* there is no verdict);
this says *what* the tool does and refuses to do, so an operator — or an auditor —
can see the envelope without reading the code.
"""

from __future__ import annotations

from typing import Any

from .integrity import COGVERITAS_ENGINE

# What the tool does. Each entry is a concrete, shipped analyst capability.
_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "verifiability",
        "does": "Splits an account into externally checkable claims vs unverifiable "
        "assertions, in Ukrainian, Russian and English.",
    },
    {
        "id": "corroboration_worklist",
        "does": "Routes each checkable claim to the concrete external record that "
        "would confirm or refute it (telecom, CCTV, bank, border, documents).",
    },
    {
        "id": "interview_questions",
        "does": "Proposes follow-up questions (Verifiability Approach / SUE) to elicit "
        "checkable detail that closes verifiability gaps — never accusatory.",
    },
    {
        "id": "timeline",
        "does": "Orders time-anchored claims chronologically; marks relative times "
        "as approximate.",
    },
    {
        "id": "inconsistencies",
        "does": "Flags review-worthy conflicts within one account (opposite polarity, "
        "figure mismatch) — pointers to check, not proof of falsity.",
    },
    {
        "id": "cross_witness",
        "does": "Compares statements across speakers: cross-witness contradictions and "
        "mutual corroborations; per-speaker verifiability profiles.",
    },
    {
        "id": "entity_index",
        "does": "Clusters inflected name mentions into a case entity index with a "
        "mention count and claim references.",
    },
    {
        "id": "reality_monitoring",
        "does": "Profiles each claim's detail richness (Reality Monitoring criteria) "
        "as a review aid — richer detail is easier to check, never a truth score.",
    },
    {
        "id": "case_tracking",
        "does": "Records the analyst's corroboration status (pending/confirmed/refuted) "
        "per item and tallies verification progress.",
    },
    {
        "id": "ingestion",
        "does": "Ingests real transcripts (SRT/VTT/CSV/JSON) with speaker attribution, "
        "as well as pasted text.",
    },
    {
        "id": "dossier",
        "does": "Exports a printable, provenanced analyst dossier.",
    },
    {
        "id": "integrity",
        "does": "Stamps a deterministic, tamper-evident chain-of-custody fingerprint "
        "and can reproduce/verify it from the source.",
    },
)

# What the tool never does. Structurally enforced, not policy.
_HARD_LIMITS: tuple[str, ...] = (
    "Never emits a person-level verdict — 'verdict' is structurally null.",
    "Never outputs a deception/lie probability or score; it is not a lie detector.",
    "Never decides whether a claim is true — only whether it is externally checkable.",
    "Emits no calibrated probability out of domain (cross-domain calibration is not demonstrated).",
    "Every finding is a pointer for human review; a human, not the system, concludes.",
    "No audio/video/physiological inference — text only.",
)


def capabilities_envelope() -> dict[str, Any]:
    """The structured capability/limits envelope."""
    return {
        "engine": COGVERITAS_ENGINE,
        "purpose": "A human-review evidence assistant for testimony: it structures "
        "claims, routes corroboration, and preserves provenance — it never judges a person.",
        "capabilities": [dict(c) for c in _CAPABILITIES],
        "hard_limits": list(_HARD_LIMITS),
        "human_in_the_loop": True,
        "supported_languages": ["uk", "ru", "en"],
        "supported_inputs": ["text", "srt", "vtt", "csv", "json"],
    }
