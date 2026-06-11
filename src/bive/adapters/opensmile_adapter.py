from __future__ import annotations

import shutil
from pathlib import Path

from .base import AdapterResult, run_adapter_command


def extract_opensmile(
    audio_path: str | Path,
    output_csv: str | Path,
    config: str = "eGeMAPSv02",
    *,
    timeout_seconds: int = 300,
) -> AdapterResult:
    exe = shutil.which("SMILExtract")
    if exe is None:
        return AdapterResult(False, "opensmile", None, "SMILExtract executable not found")
    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "-C", config, "-I", str(audio_path), "-csvoutput", str(output)]
    return run_adapter_command(
        "opensmile",
        cmd,
        output,
        "acoustic features extracted",
        timeout_seconds=timeout_seconds,
    )
