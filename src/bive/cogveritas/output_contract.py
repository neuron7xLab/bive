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


CorroborationStatus = Literal["pending", "confirmed", "refuted"]


class WorklistItem(BaseModel):
    """One checkable claim routed to the record types that would corroborate it.

    ``quote`` is verbatim user evidence (like ``ProvenanceNode.text``), not the
    system's framing; ``record_types`` are fixed system labels naming *where to
    look*. ``status``/``note`` record the *analyst's* corroboration finding against
    external records — set by a human, never inferred by the system. Neither the
    routing nor a status is a person-level verdict.
    """

    model_config = ConfigDict(extra="forbid")
    claim_id: str
    quote: str
    record_types: list[str] = []
    status: CorroborationStatus = "pending"
    note: str = ""


class VerificationProgress(BaseModel):
    """How much of the checkable account a human has corroborated so far."""

    model_config = ConfigDict(extra="forbid")
    total: int = 0
    confirmed: int = 0
    refuted: int = 0
    pending: int = 0


class RMProfile(BaseModel):
    """Per-claim Reality Monitoring detail profile — richness flags, not truth.

    Which detail criteria a claim carries (temporal/spatial/perceptual/quantitative)
    plus the reversed cognitive-operations marker. Richer detail is easier to check,
    never more likely true; this is an ordinal review aid, not a probability.
    """

    model_config = ConfigDict(extra="forbid")
    claim_id: str
    temporal: bool = False
    spatial: bool = False
    perceptual: bool = False
    quantitative: bool = False
    cognitive_operations: bool = False
    detail_count: int = 0


class InterviewQuestion(BaseModel):
    """A follow-up the interviewer could ask to elicit checkable detail.

    A prompt to gather more verifiable information (Verifiability Approach), never
    an accusation or a judgment about the person.
    """

    model_config = ConfigDict(extra="forbid")
    claim_id: str
    question: str
    rationale: str = ""


class TimelineEntry(BaseModel):
    """A time-anchored claim in chronological order. ``quote`` is verbatim evidence."""

    model_config = ConfigDict(extra="forbid")
    claim_id: str
    quote: str
    time_label: str = ""
    resolved: bool = False


class ConflictItem(BaseModel):
    """A review-worthy inconsistency between two claims — a pointer, not a verdict.

    ``quotes`` are verbatim user evidence. The item flags that two claims disagree
    (negation polarity or a figure mismatch) for a human to check; it never states
    which is true or that anyone lied.
    """

    model_config = ConfigDict(extra="forbid")
    type: Literal["negation_polarity", "figure_mismatch"]
    claim_ids: list[str]
    quotes: list[str]


class EntityRef(BaseModel):
    """A named entity clustered from its inflected mentions across the case.

    ``canonical`` is a representative surface form; ``forms`` are the observed
    variants; ``claim_ids`` index where it appears. An occurrence index, not a
    judgment about the entity.
    """

    model_config = ConfigDict(extra="forbid")
    canonical: str
    forms: list[str] = []
    count: int = 0
    claim_ids: list[str] = []


class SpeakerProfile(BaseModel):
    """Per-speaker verifiability load: checkable vs unverifiable claims.

    A review-load indicator (how much of this account can be checked externally),
    never a credibility or truthfulness score for the speaker.
    """

    model_config = ConfigDict(extra="forbid")
    speaker: str
    total: int = 0
    checkable: int = 0
    unverifiable: int = 0


class CrossWitnessItem(BaseModel):
    """A cross-speaker relation — a contradiction to resolve or a corroboration.

    ``quotes`` are verbatim evidence from two *different* speakers. A corroboration
    means two independent accounts assert the same checkable detail (stronger than
    one source); a contradiction means they conflict. Neither is a verdict.
    """

    model_config = ConfigDict(extra="forbid")
    type: Literal["cross_contradiction", "cross_corroboration"]
    speakers: list[str]
    quotes: list[str]


class IntegrityBlock(BaseModel):
    """Deterministic, reproducible fingerprint for chain-of-custody.

    Anyone with the source text can regenerate the review and confirm these
    hashes; a single altered character changes them. No timestamps enter the hash.
    """

    model_config = ConfigDict(extra="forbid")
    engine: str = ""
    source_sha256: str = ""
    analysis_sha256: str = ""
    case_id: str = ""


class COGVERITASOutput(BaseModel):
    """The public output. ``verdict`` is always ``None`` — structurally."""

    model_config = ConfigDict(extra="forbid")

    verifiability_gap: VerifiabilityGap
    rm_criteria_flagged: list[str] = []
    corroboration_questions: list[str]
    corroboration_worklist: list[WorklistItem] = []
    interview_questions: list[InterviewQuestion] = []
    verification_progress: VerificationProgress = VerificationProgress()
    timeline: list[TimelineEntry] = []
    conflicts: list[ConflictItem] = []
    entities: list[EntityRef] = []
    rm_profiles: list[RMProfile] = []
    witnesses: list[str] = []
    speaker_profiles: list[SpeakerProfile] = []
    cross_witness: list[CrossWitnessItem] = []
    calibrated_probability: float | None = None
    calibration_ci: tuple[float, float] | None = None
    calibration_ece: float | None = None
    ordinal_flag: OrdinalFlag
    audit_trail: list[ProvenanceNode]
    detected_language: str = "en"
    integrity: IntegrityBlock = IntegrityBlock()
    verdict: None = None

    @model_validator(mode="after")
    def _enforce_invariants(self) -> COGVERITASOutput:
        if self.verdict is not None:
            raise ValueError("no-verdict invariant violated: verdict must be None")
        if not self.corroboration_questions:
            raise ValueError("corroboration_questions are mandatory")
        if not self.audit_trail:
            raise ValueError("audit_trail is mandatory")
        # Probabilities are gated on demonstrated calibration — enforced HERE, at the
        # type boundary, so a probability cannot escape by constructing the class
        # directly (the build_output helper is not the only construction path).
        if self.calibrated_probability is not None:
            if self.calibration_ci is None:
                raise ValueError("calibrated_probability requires a calibration_ci")
            if self.calibration_ece is None:
                raise ValueError("calibrated_probability requires calibration_ece evidence")
            if self.calibration_ece >= ECE_THRESHOLD:
                raise ValueError(
                    "calibrated_probability requires demonstrated calibration "
                    f"(ece {self.calibration_ece} >= threshold {ECE_THRESHOLD})"
                )
        if self.calibration_ci is not None and self.calibrated_probability is None:
            raise ValueError("calibration_ci requires a calibrated_probability")
        if self.calibration_ece is not None and self.calibrated_probability is None:
            raise ValueError("calibration_ece requires a calibrated_probability")
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
    corroboration_worklist: list[WorklistItem] | None = None,
    interview_questions: list[InterviewQuestion] | None = None,
    timeline: list[TimelineEntry] | None = None,
    conflicts: list[ConflictItem] | None = None,
    entities: list[EntityRef] | None = None,
    rm_profiles: list[RMProfile] | None = None,
    witnesses: list[str] | None = None,
    speaker_profiles: list[SpeakerProfile] | None = None,
    cross_witness: list[CrossWitnessItem] | None = None,
    detected_language: str = "en",
    calibrated_probability: float | None = None,
    calibration_ci: tuple[float, float] | None = None,
    ece: float | None = None,
) -> COGVERITASOutput:
    """Construct an output, disabling probabilities when calibration is not demonstrated."""
    prob = calibrated_probability
    ci = calibration_ci
    kept_ece = ece
    if ece is None or ece >= ECE_THRESHOLD:
        # Calibration not demonstrated -> ordinal flags only.
        prob = None
        ci = None
        kept_ece = None
    ordinal: OrdinalFlag = {
        "elevated": "markers_elevated",
        "nominal": "markers_nominal",
        "insufficient": "insufficient_data",
    }[verifiability_gap]  # type: ignore[assignment]
    worklist = corroboration_worklist or []
    progress = VerificationProgress(
        total=len(worklist),
        confirmed=sum(1 for w in worklist if w.status == "confirmed"),
        refuted=sum(1 for w in worklist if w.status == "refuted"),
        pending=sum(1 for w in worklist if w.status == "pending"),
    )
    return COGVERITASOutput(
        verifiability_gap=verifiability_gap,
        rm_criteria_flagged=rm_criteria_flagged or [],
        corroboration_questions=corroboration_questions,
        corroboration_worklist=worklist,
        interview_questions=interview_questions or [],
        verification_progress=progress,
        timeline=timeline or [],
        conflicts=conflicts or [],
        entities=entities or [],
        rm_profiles=rm_profiles or [],
        witnesses=witnesses or [],
        speaker_profiles=speaker_profiles or [],
        cross_witness=cross_witness or [],
        calibrated_probability=prob,
        calibration_ci=ci,
        calibration_ece=kept_ece,
        ordinal_flag=ordinal,
        audit_trail=audit_trail,
        detected_language=detected_language,
        verdict=None,
    )
