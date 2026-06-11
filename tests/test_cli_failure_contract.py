from __future__ import annotations

import sys
from pathlib import Path

from bive.cli import main


def run_cli(monkeypatch, capsys, *args: str):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(sys, "argv", ["bive", *args])
    code = main()
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_cli_missing_input_is_controlled_error(tmp_path: Path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    output = tmp_path / "report.json"
    code, _stdout, stderr = run_cli(
        monkeypatch, capsys, "analyze", "--input", str(tmp_path / "missing.json"), "--output", str(output)
    )
    assert code == 2
    assert "BIVE_ERROR INPUT_NOT_FOUND" in stderr
    assert "Traceback" not in stderr


def test_cli_invalid_json_is_controlled_error(tmp_path: Path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    output = tmp_path / "report.json"
    code, _stdout, stderr = run_cli(
        monkeypatch, capsys, "analyze", "--input", str(bad), "--output", str(output)
    )
    assert code == 2
    assert "BIVE_ERROR INVALID_JSON" in stderr
    assert "Traceback" not in stderr
