from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from bive.adapters.base import run_adapter_command
from bive.adapters.openface_adapter import extract_openface
from bive.adapters.opensmile_adapter import extract_opensmile
from bive.adapters.whisper_adapter import transcribe_with_whisper


def test_adapter_command_timeout_returns_structured_failure(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["tool"], timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = run_adapter_command("tool", ["tool"], Path("out"), "ok", timeout_seconds=1)
    assert result.ok is False
    assert result.output_path is None
    assert "timed out" in result.message


def test_adapter_command_truncates_unbounded_stderr(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["tool"], returncode=2, stderr="x" * 3000, stdout=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = run_adapter_command("tool", ["tool"], Path("out"), "ok")
    assert result.ok is False
    assert len(result.message) == 2000


def test_media_adapters_fail_closed_when_executable_missing(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("shutil.which", lambda _name: None)
    assert extract_openface(tmp_path / "v.mp4", tmp_path / "out").ok is False
    assert extract_opensmile(tmp_path / "a.wav", tmp_path / "out.csv").ok is False
    assert transcribe_with_whisper(tmp_path / "a.wav", tmp_path / "out").ok is False


def test_media_adapter_success_path_uses_timeout(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    seen: dict[str, Any] = {}

    def fake_which(name: str) -> str | None:
        return "/bin/echo" if name == "whisper" else None

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen["timeout"] = kwargs.get("timeout")
        return subprocess.CompletedProcess(args=list(args), returncode=0, stderr="", stdout="ok")

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = transcribe_with_whisper(tmp_path / "a.wav", tmp_path / "out", timeout_seconds=7)
    assert result.ok is True
    assert seen["timeout"] == 7
