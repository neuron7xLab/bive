from __future__ import annotations

import shutil
from pathlib import Path

from .base import AdapterResult, run_adapter_command


def transcribe_with_whisper(
    media_path: str | Path,
    output_dir: str | Path,
    *,
    timeout_seconds: int = 300,
) -> AdapterResult:
    exe = shutil.which("whisper")
    if exe is None:
        return AdapterResult(
            False, "whisper", None, "whisper executable not found; install optional media extras"
        )
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    cmd = [exe, str(media_path), "--output_dir", str(out), "--output_format", "json"]
    return run_adapter_command(
        "whisper",
        cmd,
        out,
        "transcription completed",
        timeout_seconds=timeout_seconds,
    )
