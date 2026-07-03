"""COGVERITAS output contract — the no-verdict invariant, hardcoded.

The system never emits a person-level judgment. It reports which claims are
externally checkable, how uncertain it is, and what to corroborate. ``verdict``
is structurally ``None`` and cannot be set. Calibrated probabilities are only
allowed when calibration is demonstrated (ECE < the policy threshold); otherwise
the output degrades to ordinal flags. These rules are enforced at construction,
not by convention.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

# Verbatim user quotes are wrapped in guillemets by the generators; they are
# evidence (provenance), not the system's judgment, so they are stripped before
# the forbidden-judgment scan. The invariant binds the system's OWN framing.
_QUOTE_SPAN = re.compile(r"«[^»]*»")

# Release blocker: any of these appearing in a COGVERITAS output surface is a
# person-level judgment and is forbidden. The scanner in scripts/no_verdict_check
# enforces this across code and artifacts too.
FORBIDDEN_JUDGMENT_STRINGS: tuple[str, ...] = (
    "liar",
    "truthful person",
    "guilty",
    "deceptive person",
    "lie detected",
    "truth detected",
    "is lying",
    "is truthful",
    "person is deceptive",
)

# The only sanctioned framings. Never a verdict.
VerifiabilityGap = Literal["elevated", "nominal", "insufficient"]
OrdinalFlag = Literal["markers_elevated", "markers_nominal", "insufficient_data"]

# Calibration policy: probabilities are meaningless unless calibrated.
ECE_THRESHOLD = 0.10


def contains_forbidden_judgment(text: str) -> list[str]:
    """Return any forbidden person-level judgment substrings found in ``text``."""
    lowered = text.lower()
    return [s for s in FORBIDDEN_JUDGMENT_STRINGS if s in lowered]


class ProvenanceNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    text: str
    verifiability: Literal["externally_checkable", "not_externally_checkable", "insufficient_context"]
    entities: list[str] = []
    activity: str = "verifiability_tagging"
    agent: str = "bive.cogveritas.verifiability_tagger"


class COGVERITASOutput(BaseModel):
    """The public output. ``verdict`` is always ``None`` — structurally."""

    model_config = ConfigDict(extra="forbid")

    verifiability_gap: VerifiabilityGap
    rm_criteria_flagged: list[str] = []
    corroboration_questions: list[str]
    calibrated_probability: float | None = None
    calibration_ci: tuple[float, float] | None = None
    ordinal_flag: OrdinalFlag
    audit_trail: list[ProvenanceNode]
    verdict: None = None

    @model_validator(mode="after")
    def _enforce_invariants(self) -> COGVERITASOutput:
        if self.verdict is not None:
            raise ValueError("no-verdict invariant violated: verdict must be None")
        if not self.corroboration_questions:
            raise ValueError("corroboration_questions are mandatory")
        if not self.audit_trail:
            raise ValueError("audit_trail is mandatory")
        # Probabilities are gated on demonstrated calibration.
        if self.calibrated_probability is not None and self.calibration_ci is None:
            raise ValueError("calibrated_probability requires a calibration_ci")
        if self.calibration_ci is not None and self.calibrated_probability is None:
            raise ValueError("calibration_ci requires a calibrated_probability")
        # No forbidden person-level judgment in the SYSTEM's own framing. Verbatim
        # user quotes («…») are evidence, not judgment, and are stripped first.
        for field in (*self.rm_criteria_flagged, *self.corroboration_questions):
            system_framing = _QUOTE_SPAN.sub("«…»", field)
            hits = contains_forbidden_judgment(system_framing)
            if hits:
                raise ValueError(f"forbidden person-level judgment string(s): {hits}")
        return self


def build_output(
    verifiability_gap: VerifiabilityGap,
    corroboration_questions: list[str],
    audit_trail: list[ProvenanceNode],
    *,
    rm_criteria_flagged: list[str] | None = None,
    calibrated_probability: float | None = None,
    calibration_ci: tuple[float, float] | None = None,
    ece: float | None = None,
) -> COGVERITASOutput:
    """Construct an output, disabling probabilities when calibration is not demonstrated."""
    prob = calibrated_probability
    ci = calibration_ci
    if ece is None or ece >= ECE_THRESHOLD:
        # Calibration not demonstrated -> ordinal flags only.
        prob = None
        ci = None
    ordinal: OrdinalFlag = {
        "elevated": "markers_elevated",
        "nominal": "markers_nominal",
        "insufficient": "insufficient_data",
    }[verifiability_gap]  # type: ignore[assignment]
    return COGVERITASOutput(
        verifiability_gap=verifiability_gap,
        rm_criteria_flagged=rm_criteria_flagged or [],
        corroboration_questions=corroboration_questions,
        calibrated_probability=prob,
        calibration_ci=ci,
        ordinal_flag=ordinal,
        audit_trail=audit_trail,
        verdict=None,
    )
