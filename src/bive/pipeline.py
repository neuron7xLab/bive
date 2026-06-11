from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .ingest import TranscriptSegment
from .models import VerificationReport
from .report import build_report_from_segments


def parse_transcript_payload(payload: dict[str, Any]) -> list[TranscriptSegment]:
    raw_segments = payload.get("segments")
    if not isinstance(raw_segments, list):
        raise ValueError("payload must contain a list field: segments")
    segments: list[TranscriptSegment] = []
    for i, item in enumerate(raw_segments):
        if not isinstance(item, dict):
            raise ValueError(f"segment {i} must be an object")
        text = str(item.get("text", "")).strip()
        if not text:
            raise ValueError(f"segment {i} has empty text")
        segments.append(
            TranscriptSegment(
                speaker=str(item.get("speaker", "unknown")),
                text=text,
                start=float(item["start"])
                if "start" in item and item["start"] is not None
                else None,
                end=float(item["end"]) if "end" in item and item["end"] is not None else None,
            )
        )
    return segments


def analyze_transcript_payload(
    payload: dict[str, Any], subject_scope: str = "single_session"
) -> VerificationReport:
    report = build_report_from_segments(
        parse_transcript_payload(payload), subject_scope=subject_scope
    )
    # deterministic enough for tests while avoiding id collisions in API usage
    object.__setattr__(report, "report_id", f"bive-report-{uuid.uuid4().hex[:12]}")
    return report


def analyze_transcript_file(
    path: str | Path, subject_scope: str = "single_session"
) -> VerificationReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return analyze_transcript_payload(payload, subject_scope=subject_scope)
