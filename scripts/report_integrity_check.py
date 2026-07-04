"""Report content-digest integrity gate.

Every committed verification report must carry a content_digest that actually matches its
substantive content, and the report generator must stamp a valid digest on fresh output.
This is tamper-evidence: a report shared or stored can be checked against its digest, and
a single altered claim/signal/hypothesis/status breaks it. Fail-closed on any mismatch.

Emits REPORT_INTEGRITY.json.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "demo_transcript.json"
OUT = ROOT / "artifacts" / "verification" / "REPORT_INTEGRITY.json"

# A committed file is a verification report if it carries these structural keys.
_REPORT_KEYS = {"report_id", "policy_invariants", "final_status", "content_digest"}


def _is_report(data: Any) -> bool:
    return isinstance(data, dict) and _REPORT_KEYS.issubset(data.keys())


def check() -> tuple[list[str], int]:
    from bive.integrity import content_digest, verify_content_digest
    from bive.pipeline import analyze_transcript_payload

    problems: list[str] = []

    # 1) every committed report instance has a digest that matches its content.
    checked = 0
    for path in sorted(glob.glob(str(ROOT / "**" / "*.json"), recursive=True)):
        if "/.git/" in path or "egg-info" in path:
            continue
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not _is_report(data):
            continue
        checked += 1
        rel = Path(path).relative_to(ROOT).as_posix()
        if not verify_content_digest(data):
            problems.append(f"{rel}: content_digest does not match content (tampered or stale)")

    # 2) the generator stamps a valid, content-addressed digest on fresh output.
    if SAMPLE.is_file():
        report = analyze_transcript_payload(json.loads(SAMPLE.read_text(encoding="utf-8")))
        payload = report.to_dict()
        if not verify_content_digest(payload):
            problems.append("freshly generated report has an invalid content_digest")
        # 3) negative control: a mutated report must fail verification.
        tampered = dict(payload)
        tampered["final_assessment"] = str(tampered.get("final_assessment", "")) + " [ALTERED]"
        if verify_content_digest(tampered):
            problems.append("content_digest did not detect an altered final_assessment")
        # 4) the digest ignores volatile record fields (id/time), not content.
        moved = dict(payload)
        moved["report_id"] = "bive-report-different0"
        moved["created_at"] = "1999-01-01T00:00:00Z"
        if content_digest(moved) != content_digest(payload):
            problems.append("content_digest changed when only report_id/created_at changed")

    return problems, checked


def main() -> int:
    problems, checked = check()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "pass" if not problems else "fail",
                "committed_reports_checked": checked,
                "properties": [
                    "committed reports carry a matching content_digest",
                    "generated reports are stamped with a valid content_digest",
                    "a tampered report fails verification",
                    "the digest ignores report_id/created_at",
                ],
                "problems": problems,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if problems:
        for problem in problems:
            print(f"REPORT_INTEGRITY_ISSUE {problem}")
        print(f"REPORT_INTEGRITY_FAIL {len(problems)} issue(s)")
        return 1
    print(f"REPORT_INTEGRITY_PASS {checked} committed report(s) verified; generation stamps a valid digest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
