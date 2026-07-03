"""COGVERITAS — fail-closed external-fact verifiability layer over BIVE.

Not a lie detector. It forces claims onto an external-checkability path
(verifiability → provenance → calibration → bias audit → corroboration) and
never emits a person-level verdict. See docs/methodology/COGVERITAS_METHOD_ACT.md.
"""

from __future__ import annotations

from .output_contract import (
    ECE_THRESHOLD,
    FORBIDDEN_JUDGMENT_STRINGS,
    COGVERITASOutput,
    ProvenanceNode,
    build_output,
    contains_forbidden_judgment,
)
from .verifiability_tagger import (
    VerifiabilityFeatures,
    analyze,
    build_feature_vector,
    classify_claim_verifiability,
    segment_claims,
    segment_sentences,
)

KILL_AUC = 0.60

__all__ = [
    "COGVERITASOutput",
    "ECE_THRESHOLD",
    "FORBIDDEN_JUDGMENT_STRINGS",
    "KILL_AUC",
    "ProvenanceNode",
    "VerifiabilityFeatures",
    "analyze",
    "build_feature_vector",
    "build_output",
    "classify_claim_verifiability",
    "contains_forbidden_judgment",
    "segment_claims",
    "segment_sentences",
]
