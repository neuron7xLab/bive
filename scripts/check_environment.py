from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_BINARIES = ("git",)
REQUIRED_MODULES = ("pip",)


def _inside_virtualenv() -> bool:
    return bool(os.environ.get("VIRTUAL_ENV")) or sys.prefix != sys.base_prefix


def main() -> int:
    errors: list[str] = []
    if not _inside_virtualenv():
        errors.append(
            "Active virtual environment undetected. Run: python3 -m venv .venv && "
            ". .venv/bin/activate && make verify-release"
        )
    for binary in REQUIRED_BINARIES:
        if shutil.which(binary) is None:
            errors.append(f"Required binary missing from PATH: {binary}")
    for module in REQUIRED_MODULES:
        if importlib.util.find_spec(module) is None:
            errors.append(f"Required Python module missing: {module}")
    if errors:
        for error in errors:
            print(f"ENVIRONMENT_PRECHECK_FAIL {error}", file=sys.stderr)
        return 1
    print(f"ENVIRONMENT_PRECHECK_PASS python={sys.executable} root={ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
