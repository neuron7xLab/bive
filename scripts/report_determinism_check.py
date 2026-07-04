"""Report determinism + content-addressing gate.

BIVE's value proposition is *reviewable* evidence: two auditors who analyze the same
transcript must get the same report. This gate proves that the analysis is a pure
function of the input — running the pipeline twice on the canonical sample transcript
yields byte-identical substantive content (everything except the ``created_at``
timestamp), and the ``report_id`` is the content digest, so it is stable across runs
and changes iff the analysis changes. A different transcript must yield a different id.

Any drift (hidden nondeterminism — set ordering, dict iteration, uncontrolled
randomness — or a non-content-addressed id) fails the gate. Emits REPORT_DETERMINISM.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "demo_transcript.json"
OUT = ROOT / "artifacts" / "verification" / "REPORT_DETERMINISM.json"

_VOLATILE = ("created_at",)


def _substantive(report: Any) -> dict[str, Any]:
    payload = dict(report.to_dict())
    for key in _VOLATILE:
        payload.pop(key, None)
    return payload


def check(payload: dict[str, Any]) -> list[str]:
    """Return determinism/content-addressing violations for a transcript payload."""
    from bive.pipeline import _content_report_id, analyze_transcript_payload

    problems: list[str] = []
    r1 = analyze_transcript_payload(payload)
    r2 = analyze_transcript_payload(payload)

    s1 = json.dumps(_substantive(r1), sort_keys=True, ensure_ascii=False)
    s2 = json.dumps(_substantive(r2), sort_keys=True, ensure_ascii=False)
    if s1 != s2:
        problems.append("substantive report content differs across two runs — analysis is nondeterministic")

    if r1.report_id != r2.report_id:
        problems.append(f"report_id not stable across runs ({r1.report_id} != {r2.report_id})")

    # The id must actually be the content digest, not merely stable-by-luck.
    recomputed = f"bive-report-{_content_report_id(r1)}"
    if r1.report_id != recomputed:
        problems.append(f"report_id {r1.report_id} is not the content digest {recomputed} — not content-addressed")

    # A changed analysis must change the id (negative control).
    mutated = json.loads(json.dumps(payload))
    segs = mutated.get("segments")
    if isinstance(segs, list) and segs:
        segs[0] = {**segs[0], "text": str(segs[0].get("text", "")) + " (materially different claim added)."}
        r3 = analyze_transcript_payload(mutated)
        if r3.report_id == r1.report_id:
            problems.append("a materially different transcript produced the same report_id — id is not sensitive to content")

    return problems


def main() -> int:
    if not SAMPLE.is_file():
        print(f"REPORT_DETERMINISM_FAIL sample transcript absent: {SAMPLE}")
        return 1
    payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
    problems = check(payload)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "pass" if not problems else "fail",
                "sample": "samples/demo_transcript.json",
                "properties": [
                    "substantive content is a pure function of the input",
                    "report_id is content-addressed and stable across runs",
                    "report_id changes when the analysis changes",
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
            print(f"REPORT_DETERMINISM_ISSUE {problem}")
        print(f"REPORT_DETERMINISM_FAIL {len(problems)} issue(s)")
        return 1
    print("REPORT_DETERMINISM_PASS analysis is a pure function of the input; report id is content-addressed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
