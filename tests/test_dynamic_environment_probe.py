from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
def test_dynamic_environment_probe_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dynamic_environment_probe.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "DYNAMIC_ENVIRONMENT_PROBE_PASS" in result.stdout
    artifact = Path("artifacts/verification/DYNAMIC_ENVIRONMENT_PROBE.json")
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["repeated_runs"] == "pass"
    assert data["storage_concurrent_writes"] == 24
    assert data["production_auth_missing"]["status_code"] in {401, 503}
