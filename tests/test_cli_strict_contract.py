from __future__ import annotations

import json
import sys

from bive.cli import main


def run_cli(monkeypatch, capsys, *args: str):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(sys, "argv", ["bive", *args])
    code = main()
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_eval_missing_required_fields_returns_controlled_error(tmp_path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    inp = tmp_path / "bad_eval.json"
    inp.write_text(json.dumps({"labels": [1, 0]}), encoding="utf-8")
    code, _stdout, stderr = run_cli(monkeypatch, capsys, "eval", "--input", str(inp))
    assert code == 2
    assert "BIVE_ERROR INVALID_EVAL_SCHEMA" in stderr
    assert "Traceback" not in stderr


def test_eval_length_mismatch_returns_controlled_error(tmp_path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    inp = tmp_path / "bad_eval.json"
    inp.write_text(json.dumps({"labels": [1, 0], "predictions": [1]}), encoding="utf-8")
    code, _stdout, stderr = run_cli(monkeypatch, capsys, "eval", "--input", str(inp))
    assert code == 2
    assert "BIVE_ERROR INVALID_EVAL_SCHEMA" in stderr
    assert "Traceback" not in stderr
