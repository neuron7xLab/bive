"""Universal, dependency-free transcript ingestion.

BIVE's analysis core consumes a single canonical shape::

    {"subject_scope": <str>, "segments": [{"speaker", "text", "start", "end"}, ...]}

Real transcripts arrive in many shapes: subtitle files (SRT / WebVTT),
speaker-labelled plain text, spreadsheets exported to CSV, JSON Lines, and the
JSON emitted by ASR tools such as Whisper. This module turns any of those into
the canonical payload with pure, deterministic parsers and no third-party
dependencies. Detection is conservative: an unrecognised or ambiguous input
raises :class:`TranscriptFormatError` rather than guessing silently.

Every parser is a total function of its input text: the same bytes always yield
the same segments, which keeps the downstream evidence graph reproducible.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
from collections.abc import Callable, Mapping
from typing import Any

__all__ = [
    "SUPPORTED_FORMATS",
    "TranscriptDecodeError",
    "TranscriptFormatError",
    "detect_format",
    "parse_transcript",
    "supported_formats",
]

# Ordered by preference for the UI / docs; each maps to a parser below.
SUPPORTED_FORMATS: tuple[str, ...] = ("json", "jsonl", "srt", "vtt", "csv", "txt")

_DEFAULT_SUBJECT_SCOPE = "single_session"
_DEFAULT_SPEAKER = "unknown"

# "Name: spoken text" with a short, human-plausible speaker label. Kept narrow so
# that ordinary sentences containing a colon are not mistaken for speaker turns.
_SPEAKER_PREFIX = re.compile(r"^(?P<speaker>[\w .'\-]{1,40}?)\s*:\s+(?P<text>\S.*)$")

# WebVTT voice span: <v Speaker>text</v> with optional dot-separated cue classes
# (<v.loud.first Speaker>). The class token is `[\w-]+` (no dot) so the repeated
# group is unambiguous — a dotted char class here would allow exponential
# backtracking (ReDoS) on attacker-controlled cue text.
_VTT_VOICE = re.compile(r"^<v(?:\.[\w-]+)*\s+(?P<speaker>[^>]+)>(?P<text>.*?)(?:</v>)?$")

_SRT_ARROW = " --> "
_TIMECODE = re.compile(
    r"^(?:(?P<h>\d{1,2}):)?(?P<m>\d{1,2}):(?P<s>\d{1,2})(?:[.,](?P<ms>\d{1,3}))?$"
)


class TranscriptFormatError(ValueError):
    """Raised when a payload cannot be parsed into transcript segments.

    Subclasses :class:`ValueError` so the API's existing ``ValueError`` handler
    maps it to a 400 ``InvalidInput`` response without extra wiring.
    """


class TranscriptDecodeError(TranscriptFormatError):
    """Raised when a JSON/JSONL container is structurally malformed.

    Distinguished from :class:`TranscriptFormatError` so callers can preserve a
    precise "invalid JSON" error vocabulary separate from schema/shape errors.
    """


def supported_formats() -> list[str]:
    """Return the list of format identifiers accepted by :func:`parse_transcript`."""
    return list(SUPPORTED_FORMATS)


def detect_format(content: str, filename: str | None = None) -> str:
    """Infer a format identifier from an optional filename and the content.

    The filename extension is authoritative when it names a supported format;
    otherwise the content is sniffed. Detection never returns an unsupported
    identifier — it raises :class:`TranscriptFormatError` when nothing matches.
    """
    ext = _extension(filename)
    if ext in SUPPORTED_FORMATS:
        return ext
    if ext == "webvtt":
        return "vtt"
    if ext == "text":
        return "txt"

    stripped = content.lstrip("﻿ \t\r\n")
    if stripped[:6].upper().startswith("WEBVTT"):
        return "vtt"
    if stripped[:1] in "{[":
        # A single JSON document vs. JSON Lines: JSONL has multiple standalone
        # objects on separate lines, which never parses as one document.
        try:
            json.loads(content)
        except json.JSONDecodeError:
            if _looks_like_jsonl(content):
                return "jsonl"
            raise TranscriptFormatError("content starts as JSON but is not valid JSON") from None
        return "json"
    if _looks_like_jsonl(content):
        return "jsonl"
    if _looks_like_srt(stripped):
        return "srt"
    if _looks_like_csv(stripped):
        return "csv"
    if stripped:
        return "txt"
    raise TranscriptFormatError("empty input: no transcript content to parse")


def parse_transcript(
    content: str,
    fmt: str | None = None,
    filename: str | None = None,
    subject_scope: str | None = None,
) -> dict[str, Any]:
    """Parse ``content`` into the canonical analyze payload.

    ``fmt`` forces a specific parser; when ``None`` the format is auto-detected
    from ``filename`` and content. ``subject_scope`` overrides the scope carried
    by the payload (JSON inputs may embed their own; other formats default to
    ``"single_session"``).
    """
    resolved = (fmt or detect_format(content, filename)).strip().lower()
    if resolved == "webvtt":
        resolved = "vtt"
    if resolved not in SUPPORTED_FORMATS:
        raise TranscriptFormatError(
            f"unsupported format {resolved!r}; expected one of {', '.join(SUPPORTED_FORMATS)}"
        )
    parser = _PARSERS[resolved]
    scope, segments = parser(content)
    segments = [seg for seg in (_clean_segment(s) for s in segments) if seg is not None]
    if not segments:
        raise TranscriptFormatError(f"no non-empty transcript segments found in {resolved} input")
    final_scope = (subject_scope or scope or _DEFAULT_SUBJECT_SCOPE).strip() or _DEFAULT_SUBJECT_SCOPE
    return {"subject_scope": final_scope, "segments": segments}


# --------------------------------------------------------------------------- #
# Per-format parsers. Each returns (subject_scope | None, raw segment dicts).
# --------------------------------------------------------------------------- #


def _parse_json(content: str) -> tuple[str | None, list[dict[str, Any]]]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise TranscriptDecodeError(f"invalid JSON: {exc.msg} at line {exc.lineno}") from exc
    return _segments_from_json_value(data)


def _parse_jsonl(content: str) -> tuple[str | None, list[dict[str, Any]]]:
    segments: list[dict[str, Any]] = []
    for lineno, raw in enumerate(content.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TranscriptDecodeError(f"invalid JSON on line {lineno}: {exc.msg}") from exc
        if not isinstance(obj, Mapping):
            raise TranscriptFormatError(f"JSONL line {lineno} must be an object")
        segments.append(_segment_from_mapping(obj))
    return None, segments


def _parse_srt(content: str) -> tuple[str | None, list[dict[str, Any]]]:
    segments: list[dict[str, Any]] = []
    for block in re.split(r"\r?\n\s*\r?\n", content.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip() != ""]
        if not lines:
            continue
        # An optional numeric counter line precedes the timecode line.
        if lines[0].strip().isdigit() and len(lines) > 1 and _SRT_ARROW in lines[1]:
            lines = lines[1:]
        start: float | None = None
        end: float | None = None
        text_lines = lines
        if lines and _SRT_ARROW in lines[0]:
            start, end = _parse_timecode_range(lines[0])
            text_lines = lines[1:]
        speaker, text = _split_speaker(" ".join(part.strip() for part in text_lines))
        segments.append({"speaker": speaker, "text": text, "start": start, "end": end})
    return None, segments


def _parse_vtt(content: str) -> tuple[str | None, list[dict[str, Any]]]:
    body = content.lstrip("﻿")
    # Drop the WEBVTT signature line and any header block before the first cue.
    body = re.sub(r"^WEBVTT[^\n]*\n", "", body, count=1)
    segments: list[dict[str, Any]] = []
    for block in re.split(r"\r?\n\s*\r?\n", body.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip() != ""]
        if not lines:
            continue
        if lines[0].upper().startswith(("NOTE", "STYLE", "REGION")):
            continue
        # A cue may open with an identifier line before the timing line.
        if _SRT_ARROW not in lines[0] and len(lines) > 1 and _SRT_ARROW in lines[1]:
            lines = lines[1:]
        if not lines or _SRT_ARROW not in lines[0]:
            continue
        start, end = _parse_timecode_range(lines[0])
        speaker = _DEFAULT_SPEAKER
        cue_texts: list[str] = []
        for raw in lines[1:]:
            voice = _VTT_VOICE.match(raw.strip())
            if voice:
                speaker = voice.group("speaker").strip() or speaker
                cue_texts.append(_strip_tags(voice.group("text")))
            else:
                cue_texts.append(_strip_tags(raw))
        joined = " ".join(part.strip() for part in cue_texts if part.strip())
        if speaker == _DEFAULT_SPEAKER:
            speaker, joined = _split_speaker(joined)
        segments.append({"speaker": speaker, "text": joined, "start": start, "end": end})
    return None, segments


def _parse_csv(content: str) -> tuple[str | None, list[dict[str, Any]]]:
    reader = csv.reader(io.StringIO(content))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return None, []
    header = [cell.strip().lower() for cell in rows[0]]
    known = {"speaker", "text", "start", "end", "utterance", "content", "message"}
    if any(cell in known for cell in header):
        index = {name: pos for pos, name in enumerate(header)}
        text_key = next((k for k in ("text", "utterance", "content", "message") if k in index), None)
        if text_key is None:
            raise TranscriptFormatError("CSV header has no text/utterance/content/message column")
        data_rows = rows[1:]
        segments = [
            {
                "speaker": _cell(row, index.get("speaker")),
                "text": _cell(row, index.get(text_key)),
                "start": _to_float(_cell(row, index.get("start"))),
                "end": _to_float(_cell(row, index.get("end"))),
            }
            for row in data_rows
        ]
        return None, segments
    # Headerless CSV: infer columns by width. 1 col -> text; 2 -> speaker,text;
    # >=4 with numeric cols 2/3 -> speaker,text,start,end.
    segments = []
    for row in rows:
        cells = [c.strip() for c in row]
        if len(cells) == 1:
            segments.append({"speaker": _DEFAULT_SPEAKER, "text": cells[0]})
        elif len(cells) >= 4 and _to_float(cells[2]) is not None and _to_float(cells[3]) is not None:
            segments.append(
                {
                    "speaker": cells[0],
                    "text": cells[1],
                    "start": _to_float(cells[2]),
                    "end": _to_float(cells[3]),
                }
            )
        else:
            segments.append({"speaker": cells[0], "text": " ".join(cells[1:]) or cells[0]})
    return None, segments


def _parse_txt(content: str) -> tuple[str | None, list[dict[str, Any]]]:
    segments: list[dict[str, Any]] = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        speaker, text = _split_speaker(line)
        segments.append({"speaker": speaker, "text": text})
    return None, segments


_Parser = Callable[[str], "tuple[str | None, list[dict[str, Any]]]"]

_PARSERS: dict[str, _Parser] = {
    "json": _parse_json,
    "jsonl": _parse_jsonl,
    "srt": _parse_srt,
    "vtt": _parse_vtt,
    "csv": _parse_csv,
    "txt": _parse_txt,
}


# --------------------------------------------------------------------------- #
# JSON shape adapters
# --------------------------------------------------------------------------- #


def _segments_from_json_value(data: Any) -> tuple[str | None, list[dict[str, Any]]]:
    if isinstance(data, list):
        return None, [_segment_from_mapping(_require_mapping(item, idx)) for idx, item in enumerate(data)]
    if not isinstance(data, Mapping):
        raise TranscriptFormatError("JSON transcript must be an object or an array of segments")
    scope = data.get("subject_scope")
    scope_str = str(scope) if isinstance(scope, str) and scope.strip() else None
    raw_segments = data.get("segments")
    if isinstance(raw_segments, list):
        return scope_str, [
            _segment_from_mapping(_require_mapping(item, idx)) for idx, item in enumerate(raw_segments)
        ]
    # A single ASR blob with only top-level text (e.g. Whisper's `{"text": ...}`).
    if isinstance(data.get("text"), str):
        return scope_str, [_segment_from_mapping(data)]
    raise TranscriptFormatError("JSON object must contain a 'segments' list or a 'text' field")


def _segment_from_mapping(item: Mapping[str, Any]) -> dict[str, Any]:
    text = item.get("text")
    if text is None:
        text = item.get("utterance", item.get("content", item.get("message", "")))
    return {
        "speaker": item.get("speaker", item.get("channel", _DEFAULT_SPEAKER)),
        "text": text,
        "start": _to_float(item.get("start")),
        "end": _to_float(item.get("end")),
    }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _clean_segment(raw: Mapping[str, Any]) -> dict[str, Any] | None:
    text = str(raw.get("text") or "").strip()
    if not text:
        return None
    speaker = str(raw.get("speaker") or _DEFAULT_SPEAKER).strip() or _DEFAULT_SPEAKER
    segment: dict[str, Any] = {"speaker": speaker[:200], "text": text}
    start = _to_float(raw.get("start"))
    end = _to_float(raw.get("end"))
    if start is not None:
        segment["start"] = start
    if end is not None:
        segment["end"] = end
    return segment


def _split_speaker(line: str) -> tuple[str, str]:
    match = _SPEAKER_PREFIX.match(line.strip())
    if match:
        return match.group("speaker").strip(), match.group("text").strip()
    return _DEFAULT_SPEAKER, line.strip()


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


def _parse_timecode_range(line: str) -> tuple[float | None, float | None]:
    left, _, right = line.partition(_SRT_ARROW)
    return _parse_timecode(left), _parse_timecode(right)


def _parse_timecode(value: str) -> float | None:
    token = value.strip().split()[0] if value.strip() else ""
    match = _TIMECODE.match(token)
    if not match:
        return None
    hours = int(match.group("h") or 0)
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    millis_raw = match.group("ms") or "0"
    millis = int(millis_raw.ljust(3, "0")[:3])
    return hours * 3600 + minutes * 60 + seconds + millis / 1000.0


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def _require_mapping(item: Any, idx: int) -> Mapping[str, Any]:
    if not isinstance(item, Mapping):
        raise TranscriptFormatError(f"segment {idx} must be a JSON object")
    return item


def _extension(filename: str | None) -> str:
    if not filename:
        return ""
    _, _, ext = filename.rpartition(".")
    return ext.strip().lower() if ext and ext != filename else ""


def _looks_like_jsonl(content: str) -> bool:
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    if len(lines) < 1:
        return False
    objects = 0
    for line in lines:
        if not line.startswith("{"):
            return False
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            return False
        if not isinstance(parsed, Mapping):
            return False
        objects += 1
    return objects >= 1


def _looks_like_srt(content: str) -> bool:
    return _SRT_ARROW in content and bool(re.search(r"\d{1,2}:\d{2}:\d{2}", content))


def _looks_like_csv(content: str) -> bool:
    lines = [ln for ln in content.splitlines() if ln.strip()]
    if len(lines) < 1:
        return False
    delimiter = "," if "," in lines[0] else ("\t" if "\t" in lines[0] else "")
    if not delimiter:
        return False
    return all(delimiter in ln for ln in lines[: min(len(lines), 3)])
