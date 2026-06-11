from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ADAPTER_TIMEOUT_SECONDS = 300
MAX_ADAPTER_MESSAGE_CHARS = 2_000


@dataclass(frozen=True)
class AdapterResult:
    ok: bool
    tool: str
    output_path: Path | None
    message: str


def _bounded_message(value: str) -> str:
    text = value.strip()
    if len(text) <= MAX_ADAPTER_MESSAGE_CHARS:
        return text
    return text[-MAX_ADAPTER_MESSAGE_CHARS:]


def run_adapter_command(
    tool: str,
    cmd: Sequence[str],
    output_path: Path | None,
    success_message: str,
    *,
    timeout_seconds: int = DEFAULT_ADAPTER_TIMEOUT_SECONDS,
) -> AdapterResult:
    """Run an external media adapter with bounded failure behavior.

    Adapter integrations are optional and operationally unsafe when they can hang,
    emit unbounded stderr/stdout, or leak raw OSError tracebacks. This helper keeps
    all adapter failures as structured AdapterResult values.
    """
    try:
        proc = subprocess.run(
            list(cmd),
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return AdapterResult(False, tool, None, f"{tool} timed out after {timeout_seconds}s")
    except OSError as exc:
        return AdapterResult(False, tool, None, f"{tool} execution failed: {exc}")

    if proc.returncode != 0:
        message = _bounded_message(
            proc.stderr or proc.stdout or f"{tool} exited with {proc.returncode}"
        )
        return AdapterResult(False, tool, None, message)
    return AdapterResult(True, tool, output_path, success_message)
