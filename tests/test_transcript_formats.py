from __future__ import annotations

import pytest

from bive.transcript_formats import (
    SUPPORTED_FORMATS,
    TranscriptFormatError,
    detect_format,
    parse_transcript,
    supported_formats,
)

SRT = (
    "1\n"
    "00:00:00,000 --> 00:00:04,200\n"
    "Alice: I never received that money.\n"
    "\n"
    "2\n"
    "00:00:08,000 --> 00:00:12,500\n"
    "I received that money later.\n"
)

VTT = (
    "WEBVTT\n"
    "\n"
    "00:00.000 --> 00:04.200\n"
    "<v Alice>I never received that money.\n"
    "\n"
    "NOTE this cue is a comment and must be skipped\n"
    "\n"
    "00:08.000 --> 00:12.500\n"
    "<v Bob>Actually you did.\n"
)

CSV_WITH_HEADER = "speaker,text,start,end\nsubject,I did not do it,0,3.2\nsubject,Maybe I did,4,7\n"
CSV_HEADERLESS = "subject,I did not do it,0,3.2\nsubject,Maybe I did,4,7\n"
TXT = "Alice: I never did that.\nBob: You clearly did.\nA plain line with no speaker.\n"
JSONL = '{"speaker":"a","text":"line one","start":0}\n{"speaker":"b","text":"line two"}\n'
WHISPER = (
    '{"text":"full text","segments":['
    '{"start":0.0,"end":2.0,"text":"hi there"},'
    '{"start":2.0,"end":4.0,"text":"bye now"}]}'
)
BIVE_JSON = '{"subject_scope":"case_42","segments":[{"speaker":"x","text":"hello"}]}'


def test_supported_formats_is_stable() -> None:
    assert supported_formats() == list(SUPPORTED_FORMATS)
    assert "srt" in SUPPORTED_FORMATS
    assert set(SUPPORTED_FORMATS) == {"json", "jsonl", "srt", "vtt", "csv", "txt"}


@pytest.mark.parametrize(
    "content,filename,expected",
    [
        (SRT, "case.srt", "srt"),
        (VTT, "case.vtt", "vtt"),
        (CSV_WITH_HEADER, "case.csv", "csv"),
        (TXT, "case.txt", "txt"),
        (JSONL, "case.jsonl", "jsonl"),
        (BIVE_JSON, "case.json", "json"),
    ],
)
def test_detect_format_by_extension(content: str, filename: str, expected: str) -> None:
    assert detect_format(content, filename) == expected


def test_detect_format_by_content_without_filename() -> None:
    assert detect_format(VTT) == "vtt"
    assert detect_format(BIVE_JSON) == "json"
    assert detect_format(JSONL) == "jsonl"
    assert detect_format(SRT) == "srt"
    assert detect_format(CSV_WITH_HEADER) == "csv"
    assert detect_format("just plain narrative text here") == "txt"


def test_detect_format_empty_raises() -> None:
    with pytest.raises(TranscriptFormatError):
        detect_format("   \n  ")


def test_parse_srt_timecodes_and_speaker() -> None:
    payload = parse_transcript(SRT, filename="case.srt")
    assert payload["subject_scope"] == "single_session"
    segments = payload["segments"]
    assert len(segments) == 2
    assert segments[0] == {
        "speaker": "Alice",
        "text": "I never received that money.",
        "start": 0.0,
        "end": 4.2,
    }
    assert segments[1]["speaker"] == "unknown"
    assert segments[1]["start"] == 8.0


def test_parse_vtt_voice_tags_and_notes() -> None:
    payload = parse_transcript(VTT, filename="case.vtt")
    segments = payload["segments"]
    assert [s["speaker"] for s in segments] == ["Alice", "Bob"]
    assert segments[0]["end"] == 4.2
    assert all("<" not in s["text"] for s in segments)


def test_parse_csv_with_and_without_header() -> None:
    with_header = parse_transcript(CSV_WITH_HEADER, filename="c.csv")["segments"]
    headerless = parse_transcript(CSV_HEADERLESS, filename="c.csv")["segments"]
    assert with_header == headerless
    assert with_header[0] == {"speaker": "subject", "text": "I did not do it", "start": 0.0, "end": 3.2}


def test_parse_txt_speaker_inference() -> None:
    segments = parse_transcript(TXT, filename="c.txt")["segments"]
    assert len(segments) == 3
    assert segments[0]["speaker"] == "Alice"
    assert segments[2]["speaker"] == "unknown"


def test_parse_jsonl() -> None:
    segments = parse_transcript(JSONL, filename="c.jsonl")["segments"]
    assert [s["text"] for s in segments] == ["line one", "line two"]
    assert segments[0]["start"] == 0.0


def test_parse_whisper_json() -> None:
    segments = parse_transcript(WHISPER, filename="w.json")["segments"]
    assert [s["text"] for s in segments] == ["hi there", "bye now"]
    assert segments[0]["speaker"] == "unknown"


def test_parse_bive_json_preserves_scope() -> None:
    payload = parse_transcript(BIVE_JSON, filename="c.json")
    assert payload["subject_scope"] == "case_42"


def test_subject_scope_override_wins() -> None:
    payload = parse_transcript(BIVE_JSON, filename="c.json", subject_scope="override")
    assert payload["subject_scope"] == "override"


def test_json_list_of_segments() -> None:
    payload = parse_transcript('[{"text":"a"},{"text":"b"}]', filename="c.json")
    assert len(payload["segments"]) == 2


def test_determinism_same_input_same_output() -> None:
    first = parse_transcript(SRT, filename="c.srt")
    second = parse_transcript(SRT, filename="c.srt")
    assert first == second


def test_empty_segments_after_cleaning_raises() -> None:
    with pytest.raises(TranscriptFormatError):
        parse_transcript("\n\n\n", fmt="txt")


def test_invalid_json_raises_format_error() -> None:
    with pytest.raises(TranscriptFormatError):
        parse_transcript("{not valid json", fmt="json")


def test_unsupported_format_raises() -> None:
    with pytest.raises(TranscriptFormatError):
        parse_transcript("anything", fmt="pdf")


def test_forced_format_overrides_detection() -> None:
    # SRT content forced as txt yields raw lines, not timecoded segments.
    segments = parse_transcript(SRT, fmt="txt")["segments"]
    assert any("-->" in s["text"] for s in segments)


def test_whitespace_only_speaker_defaults() -> None:
    segments = parse_transcript('{"segments":[{"speaker":"   ","text":"hi"}]}', fmt="json")["segments"]
    assert segments[0]["speaker"] == "unknown"


def test_non_numeric_timecodes_become_none() -> None:
    segments = parse_transcript(
        '{"segments":[{"text":"hi","start":"abc","end":null}]}', fmt="json"
    )["segments"]
    assert "start" not in segments[0]
    assert "end" not in segments[0]


def test_srt_without_index_line() -> None:
    raw = "00:00:01,000 --> 00:00:02,000\nHello there\n"
    segments = parse_transcript(raw, fmt="srt")["segments"]
    assert segments[0]["text"] == "Hello there"
    assert segments[0]["start"] == 1.0


def test_json_object_without_segments_or_text_raises() -> None:
    with pytest.raises(TranscriptFormatError):
        parse_transcript('{"foo":"bar"}', fmt="json")


def test_webvtt_alias_normalised() -> None:
    payload = parse_transcript(VTT, fmt="webvtt")
    assert payload["segments"][0]["speaker"] == "Alice"
