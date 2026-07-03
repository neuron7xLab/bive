"""Zero-trust calibration gate.

Never trust that a code change preserved the science — re-measure the
instrument's operating characteristics on every build and fail if it drifts
below its published floors. Writes a tamper-evident evidence artifact whose
content digest covers the metric payload, so the published numbers cannot be
silently edited without invalidating the digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("BIVE_STORAGE", str(Path(tempfile.gettempdir()) / "bive-calibration.sqlite3"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bive.benchmark import full_report  # noqa: E402

ARTIFACT = ROOT / "artifacts" / "verification" / "CALIBRATION.json"


def _content_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def main() -> int:
    report = full_report()
    gate = report["gate"]
    assert isinstance(gate, dict)

    digest = _content_digest(report)
    evidence = {
        **report,
        "integrity": {
            "algorithm": "sha256",
            "content_digest": digest,
            "scope": "sha256 over the calibration payload; edits invalidate this digest",
        },
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if not gate["passed"]:
        failed = [c for c in gate["checks"] if not c["passed"]]  # type: ignore[union-attr]
        print("CALIBRATION_GATE_FAIL", file=sys.stderr)
        for check in failed:
            print(f"- {check['name']}: {check['detail']}", file=sys.stderr)
        return 1
    print(
        "CALIBRATION_GATE_PASS "
        f"auc={gate['roc_auc_ci']['point']} "  # type: ignore[index]
        f"ap={report['benchmark']['average_precision']} "  # type: ignore[index]
        f"othello={report['othello_guard']['specificity']} "  # type: ignore[index]
        f"digest={digest[:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
