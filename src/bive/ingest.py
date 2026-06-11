from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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


def load_transcript(path: str | Path) -> list[TranscriptSegment]:
    data = load_json(path)
    raw_segments = data.get("segments")
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
