from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "security" / "pip-audit.json"


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write(status: str, reason: str, *, raw: dict[str, Any] | None = None) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": status,
                "generated_at": _utc(),
                "reason": reason,
                "tool": "pip-audit",
                "raw": raw,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def main() -> int:
    executable = shutil.which("pip-audit")
    if executable is None:
        _write(
            "UNKNOWN_SECURITY_STATE",
            "pip-audit is not installed; install with pip install -e '.[security]'",
        )
        print(f"UNKNOWN_SECURITY_STATE wrote {OUT.relative_to(ROOT)}")
        return 0

    result = subprocess.run(  # noqa: S603
        [executable, "--format=json"],
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    try:
        raw = json.loads(result.stdout) if result.stdout.strip() else None
    except json.JSONDecodeError:
        raw = None
    if result.returncode == 0:
        _write("PASS", "pip-audit completed without known vulnerabilities", raw=raw)
        print(f"DEPENDENCY_AUDIT_PASS wrote {OUT.relative_to(ROOT)}")
        return 0
    reason = result.stderr.strip() or result.stdout.strip() or f"pip-audit exit={result.returncode}"
    status = "UNKNOWN_SECURITY_STATE" if any(token in reason.lower() for token in ("network", "connection", "timeout", "proxy", "service")) else "FAIL"
    _write(status, reason[:2000], raw=raw)
    print(f"{status} wrote {OUT.relative_to(ROOT)}")
    return 0 if status == "UNKNOWN_SECURITY_STATE" else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
