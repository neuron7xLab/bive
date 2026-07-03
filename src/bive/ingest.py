from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .transcript_formats import parse_transcript


@dataclass(frozen=True)
class TranscriptSegment:
    speaker: str
    text: str
    start: float | None = None
    end: float | None = None
    source_id: str = "transcript"


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    return data


def segments_from_payload(payload: dict[str, Any]) -> list[TranscriptSegment]:
    """Build :class:`TranscriptSegment` records from a canonical analyze payload."""
    raw_segments = payload.get("segments")
    if not isinstance(raw_segments, list):
        raise ValueError("Input must contain a list field: segments")
    segments: list[TranscriptSegment] = []
    for idx, item in enumerate(raw_segments):
        if not isinstance(item, dict):
            raise ValueError(f"segment {idx} must be an object")
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        segments.append(
            TranscriptSegment(
                speaker=str(item.get("speaker", "unknown")),
                text=text,
                start=item.get("start"),
                end=item.get("end"),
                source_id=str(item.get("source_id", f"segment:{idx}")),
            )
        )
    if not segments:
        raise ValueError("No non-empty transcript segments found")
    return segments


def load_transcript(path: str | Path) -> list[TranscriptSegment]:
    """Load a JSON transcript file into segments (strict ``{segments: [...]}``)."""
    return segments_from_payload(load_json(path))


def load_transcript_any(path: str | Path) -> list[TranscriptSegment]:
    """Load a transcript from any supported format (JSON, JSONL, SRT, VTT, CSV, TXT).

    The format is inferred from the file extension and content. This is the
    format-aware entry point used by the CLI and file-upload flows; the analysis
    core stays identical regardless of the source container.
    """
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    payload = parse_transcript(content, fmt=None, filename=p.name)
    return segments_from_payload(payload)
