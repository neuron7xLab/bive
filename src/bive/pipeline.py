from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .ingest import TranscriptSegment
from .models import VerificationReport
from .report import build_report_from_segments


def _content_report_id(report: VerificationReport) -> str:
    """A content-addressed report id: sha256 over the substantive analysis.

    The id is a pure function of the input transcript, NOT of wall-clock time or a
    random uuid — two auditors who analyze the same transcript get the same id, so
    reports are reproducible, deduplicable and tamper-evident (a changed analysis
    changes the id). ``report_id`` and the volatile ``created_at`` timestamp are
    excluded from the digest so the id encodes the analysis, not when it was run.
    """
    payload = report.to_dict()
    payload.pop("report_id", None)
    payload.pop("created_at", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


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
    # Content-addressed: the id is a pure function of the analysis (same transcript ->
    # same id), so reports are reproducible and tamper-evident rather than random.
    object.__setattr__(report, "report_id", f"bive-report-{_content_report_id(report)}")
    return report


def analyze_transcript_file(
    path: str | Path, subject_scope: str = "single_session"
) -> VerificationReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return analyze_transcript_payload(payload, subject_scope=subject_scope)
