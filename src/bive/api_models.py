from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_MAX_SEGMENTS = 2_000
DEFAULT_MAX_TEXT_CHARS = 10_000


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TranscriptSegmentIn(StrictModel):
    speaker: str = Field(default="unknown", max_length=200)
    text: str = Field(min_length=1, max_length=DEFAULT_MAX_TEXT_CHARS)
    start: float | None = None
    end: float | None = None


class TranscriptAnalyzeRequest(StrictModel):
    subject_scope: str = Field(default="single_session", max_length=200)
    segments: list[TranscriptSegmentIn] = Field(min_length=1, max_length=DEFAULT_MAX_SEGMENTS)


class InnerErrorResponse(StrictModel):
    requestId: str
    clientRequestId: str | None = None


class ErrorBody(StrictModel):
    code: str
    message: str
    details: list[str] = Field(default_factory=list)
    innererror: InnerErrorResponse


class ErrorResponse(StrictModel):
    error: ErrorBody


class CapabilityResponse(StrictModel):
    modalities: list[str]
    invariants: list[str]
    outputs: list[str]
    production_gates: list[str]
    optional_adapters: list[str]


class GateStatus(StrictModel):
    name: str
    command: str
    required_for_release: bool = True
    last_observed: Literal["pass", "fail", "unknown"] = "unknown"


class RuntimeLimitsResponse(StrictModel):
    max_upload_bytes: int
    max_segments: int
    max_text_chars: int
    auth_required: bool
    allow_person_level_verdicts: bool


class StorageStatsResponse(StrictModel):
    report_count: int
    audit_event_count: int
    schema_version: int
    storage_path_configured: bool


class SystemStatusResponse(StrictModel):
    service: str
    version: str
    environment: str
    readiness: Literal["ready", "not_ready"]
    config_errors: list[str]
    limits: RuntimeLimitsResponse
    storage: StorageStatsResponse
    gates: list[GateStatus]


class DesignContractResponse(StrictModel):
    product_layer: str
    interaction_model: str
    accessibility_target: str
    security_model: str
    operational_model: str
    evidence_policy: str


class ReportSummaryResponse(StrictModel):
    report_id: str
    created_at: str
    status: str
    subject_scope: str


class ReportResponse(StrictModel):
    report: dict[str, Any]
