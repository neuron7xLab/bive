from __future__ import annotations

import json
from pathlib import Path

from bive.cli import main

SRT = (
    "1\n"
    "00:00:00,000 --> 00:00:04,200\n"
    "Alice: I never received that money.\n"
    "\n"
    "2\n"
    "00:00:08,000 --> 00:00:12,500\n"
    "Alice: I received that money later.\n"
)


def test_analyze_accepts_srt(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    src = tmp_path / "case.srt"
    src.write_text(SRT, encoding="utf-8")
    out = tmp_path / "report.json"
    exit_code = _run(["analyze", "--input", str(src), "--output", str(out)])
    assert exit_code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["input_summary"]["segments"] == 2


def test_convert_srt_to_json_stdout(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    src = tmp_path / "case.srt"
    src.write_text(SRT, encoding="utf-8")
    exit_code = _run(["convert", "--input", str(src)])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["subject_scope"] == "single_session"
    assert len(payload["segments"]) == 2


def test_convert_writes_file(tmp_path: Path) -> None:
    src = tmp_path / "case.txt"
    src.write_text("Alice: hi\nBob: bye\n", encoding="utf-8")
    out = tmp_path / "canonical.json"
    exit_code = _run(["convert", "--input", str(src), "--output", str(out)])
    assert exit_code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert [s["speaker"] for s in payload["segments"]] == ["Alice", "Bob"]


def test_convert_subject_scope_override(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    src = tmp_path / "case.txt"
    src.write_text("hello world\n", encoding="utf-8")
    exit_code = _run(["convert", "--input", str(src), "--subject-scope", "night_shift"])
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["subject_scope"] == "night_shift"


def test_convert_missing_input(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = _run(["convert", "--input", str(tmp_path / "nope.srt")])
    assert exit_code == 2
    assert "INPUT_NOT_FOUND" in capsys.readouterr().err


def test_formats_lists_supported(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = _run(["formats"])
    assert exit_code == 0
    formats = json.loads(capsys.readouterr().out)["supported_formats"]
    assert {"srt", "vtt", "csv", "txt", "json", "jsonl"} == set(formats)


def _run(argv: list[str]) -> int:
    import sys

    original = sys.argv
    sys.argv = ["bive", *argv]
    try:
        return main()
    finally:
        sys.argv = original
