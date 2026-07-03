"""Transcript ingestion for the verifiability layer.

Real interrogation/interview records arrive as SRT, VTT, CSV, or JSON — not plain
prose. This flattens a structured transcript into the ``Speaker: utterance`` line
form the verifiability pipeline consumes, preserving speaker attribution (so
cross-witness analysis lights up) and collapsing timing/formatting noise.

Flattening is gated on an explicit format signal (a filename extension), so pasted
plain testimony — which may itself contain commas or colons — is never mis-parsed
as a structured transcript; it passes through untouched.
"""

from __future__ import annotations

import re

from ..transcript_formats import TranscriptFormatError, parse_transcript

_STRUCTURED = {"json", "jsonl", "srt", "vtt", "csv"}
_ANON = "unknown"
_EXT = re.compile(r"\.([a-z0-9]+)\s*$", re.IGNORECASE)


def _ext(filename: str | None) -> str | None:
    if not filename:
        return None
    m = _EXT.search(filename)
    return m.group(1).lower() if m else None


def to_statement_text(content: str, filename: str | None = None) -> str:
    """Normalize a structured transcript to ``Speaker: utterance`` lines.

    Only applied when ``filename`` names a structured format; otherwise the content
    is returned unchanged (plain text, already handled by the speaker parser). On
    any parse error the raw content is returned — ingestion never hard-fails the
    review.
    """
    ext = _ext(filename)
    if ext not in _STRUCTURED:
        return content
    try:
        payload = parse_transcript(content, ext, filename)
    except TranscriptFormatError:
        return content
    lines: list[str] = []
    for seg in payload["segments"]:
        speaker = re.sub(r"[:\n\r]+", " ", str(seg.get("speaker", ""))).strip()[:40]
        utterance = " ".join(str(seg.get("text", "")).split())
        if not utterance:
            continue
        if speaker and speaker.lower() != _ANON:
            lines.append(f"{speaker}: {utterance}")
        else:
            lines.append(utterance)
    return "\n".join(lines) if lines else content
