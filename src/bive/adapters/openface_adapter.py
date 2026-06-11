from __future__ import annotations

import shutil
from pathlib import Path

from .base import AdapterResult, run_adapter_command


def extract_openface(
    video_path: str | Path,
    output_dir: str | Path,
    *,
    timeout_seconds: int = 300,
) -> AdapterResult:
    exe = shutil.which("FeatureExtraction") or shutil.which("FaceLandmarkVidMulti")
    if exe is None:
        return AdapterResult(False, "openface", None, "OpenFace executable not found")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "-f", str(video_path), "-out_dir", str(out)]
    return run_adapter_command(
        "openface",
        cmd,
        out,
        "facial behavior features extracted",
        timeout_seconds=timeout_seconds,
    )
