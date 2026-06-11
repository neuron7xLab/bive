from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Modality(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    VISION = "vision"
    CONTEXT = "context"
    SYSTEM = "system"


class EvidenceDirection(str, Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"


class ReviewStatus(str, Enum):
    INCONCLUSIVE = "inconclusive"
    REVIEW_REQUIRED = "review_required"
    LOW_RISK = "low_risk"
    ELEVATED_RISK = "elevated_risk"
    INVALID_INPUT = "invalid_input"


def _bounded(name: str, value: float, low: float = 0.0, high: float = 1.0) -> None:
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}], got {value}")


def _reject_extra(model_name: str, data: dict[str, Any], allowed: set[str]) -> None:
    extra = sorted(set(data) - allowed)
    if extra:
        raise ValueError(f"{model_name} contains unsupported fields: {', '.join(extra)}")


@dataclass(frozen=True)
class ProvenanceRecord:
    entity_id: str
    activity: str
    agent: str
    source: str
    generated_at: str = field(default_factory=utc_now_iso)
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Claim:
    claim_id: str
    speaker: str
    text: str
    start: float | None = None
    end: float | None = None
    source_id: str = "unknown"
    qualifiers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceEvent:
    event_id: str
    source_id: str
    modality: Modality
    feature: str
    value: str | float | int | bool | dict[str, Any]
    confidence: float
    direction: EvidenceDirection = EvidenceDirection.NEUTRAL
    magnitude: float = 0.0
    timestamp_start: float | None = None
    timestamp_end: float | None = None
    hypothesis_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    provenance: ProvenanceRecord | None = None

    def __post_init__(self) -> None:
        _bounded("confidence", self.confidence)
        _bounded("magnitude", self.magnitude)
        if (
            self.timestamp_start is not None
            and self.timestamp_end is not None
            and self.timestamp_end < self.timestamp_start
        ):
            raise ValueError("timestamp_end must be >= timestamp_start")

    def weighted_score(self) -> float:
        sign = (
            1.0
            if self.direction == EvidenceDirection.SUPPORTS
            else -1.0
            if self.direction == EvidenceDirection.REFUTES
            else 0.0
        )
        return sign * self.confidence * self.magnitude

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["modality"] = self.modality.value
        data["direction"] = self.direction.value
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceEvent:
        _reject_extra(
            "EvidenceEvent",
            data,
            {
                "event_id",
                "source_id",
                "modality",
                "feature",
                "value",
                "confidence",
                "direction",
                "magnitude",
                "timestamp_start",
                "timestamp_end",
                "hypothesis_refs",
                "limitations",
                "provenance",
            },
        )
        prov = data.get("provenance")
        return cls(
            event_id=str(data["event_id"]),
            source_id=str(data["source_id"]),
            modality=Modality(data["modality"]),
            feature=str(data["feature"]),
            value=data["value"],
            confidence=float(data["confidence"]),
            direction=EvidenceDirection(data.get("direction", "neutral")),
            magnitude=float(data.get("magnitude", 0.0)),
            timestamp_start=data.get("timestamp_start"),
            timestamp_end=data.get("timestamp_end"),
            hypothesis_refs=tuple(data.get("hypothesis_refs", ())),
            limitations=tuple(data.get("limitations", ())),
            provenance=ProvenanceRecord(**prov) if isinstance(prov, dict) else None,
        )


@dataclass(frozen=True)
class Signal:
    signal_id: str
    modality: Modality
    name: str
    value: float | str | dict[str, Any]
    confidence: float
    interpretation: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _bounded("confidence", self.confidence)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["modality"] = self.modality.value
        return data


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    label: str
    description: str
    prior: float = 0.5
    evidence_for: tuple[str, ...] = ()
    evidence_against: tuple[str, ...] = ()
    score: float = 0.0
    uncertainty: float = 1.0
    status: ReviewStatus = ReviewStatus.INCONCLUSIVE
    alternative_explanations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _bounded("prior", self.prior)
        _bounded("uncertainty", self.uncertainty)
        _bounded("score", self.score)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class VerificationReport:
    report_id: str
    created_at: str
    subject_scope: str
    input_summary: dict[str, Any]
    claims: tuple[Claim, ...]
    signals: tuple[Signal, ...]
    evidence_events: tuple[EvidenceEvent, ...]
    hypotheses: tuple[Hypothesis, ...]
    final_status: ReviewStatus
    final_assessment: str
    limitations: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    verification_questions: tuple[str, ...]
    provenance: tuple[ProvenanceRecord, ...] = ()
    report_version: str = "1.0"
    policy_invariants: tuple[str, ...] = (
        "No automatic person-level liar label.",
        "No single cue may decide a hypothesis.",
        "Every elevated hypothesis must include counter-evidence or missing evidence.",
        "Human review required for real-world decisions.",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "report_version": self.report_version,
            "subject_scope": self.subject_scope,
            "input_summary": self.input_summary,
            "claims": [c.to_dict() for c in self.claims],
            "signals": [s.to_dict() for s in self.signals],
            "evidence_events": [e.to_dict() for e in self.evidence_events],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "final_status": self.final_status.value,
            "final_assessment": self.final_assessment,
            "limitations": list(self.limitations),
            "missing_evidence": list(self.missing_evidence),
            "verification_questions": list(self.verification_questions),
            "provenance": [p.to_dict() for p in self.provenance],
            "policy_invariants": list(self.policy_invariants),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationReport:
        _reject_extra(
            "VerificationReport",
            data,
            {
                "report_id",
                "created_at",
                "report_version",
                "subject_scope",
                "input_summary",
                "claims",
                "signals",
                "evidence_events",
                "hypotheses",
                "final_status",
                "final_assessment",
                "limitations",
                "missing_evidence",
                "verification_questions",
                "provenance",
                "policy_invariants",
            },
        )
        return cls(
            report_id=str(data["report_id"]),
            created_at=str(data["created_at"]),
            report_version=str(data.get("report_version", "1.0")),
            subject_scope=str(data["subject_scope"]),
            input_summary=dict(data["input_summary"]),
            claims=tuple(Claim(**c) for c in data.get("claims", [])),
            signals=tuple(
                Signal(
                    signal_id=s["signal_id"],
                    modality=Modality(s["modality"]),
                    name=s["name"],
                    value=s["value"],
                    confidence=s["confidence"],
                    interpretation=s["interpretation"],
                    limitations=tuple(s.get("limitations", ())),
                )
                for s in data.get("signals", [])
            ),
            evidence_events=tuple(
                EvidenceEvent.from_dict(e) for e in data.get("evidence_events", [])
            ),
            hypotheses=tuple(
                Hypothesis(
                    hypothesis_id=h["hypothesis_id"],
                    label=h["label"],
                    description=h["description"],
                    prior=h.get("prior", 0.5),
                    evidence_for=tuple(h.get("evidence_for", ())),
                    evidence_against=tuple(h.get("evidence_against", ())),
                    score=h.get("score", 0.0),
                    uncertainty=h.get("uncertainty", 1.0),
                    status=ReviewStatus(h.get("status", "inconclusive")),
                    alternative_explanations=tuple(h.get("alternative_explanations", ())),
                )
                for h in data.get("hypotheses", [])
            ),
            final_status=ReviewStatus(data["final_status"]),
            final_assessment=str(data["final_assessment"]),
            limitations=tuple(data.get("limitations", ())),
            missing_evidence=tuple(data.get("missing_evidence", ())),
            verification_questions=tuple(data.get("verification_questions", ())),
            provenance=tuple(ProvenanceRecord(**p) for p in data.get("provenance", [])),
            policy_invariants=tuple(data.get("policy_invariants", ())),
        )


ReportStatusLiteral = Literal[
    "inconclusive", "review_required", "low_risk", "elevated_risk", "invalid_input"
]
