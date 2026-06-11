from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from bive.ingest import TranscriptSegment
from bive.report import build_report_from_segments


def build_segments(count: int) -> list[TranscriptSegment]:
    return [
        TranscriptSegment(
            speaker="s",
            text=(
                "Я точно ніколи не бачив цей документ."
                if i % 2 == 0
                else "Можливо, бачив цей документ раніше."
            ),
            start=float(i),
            end=float(i) + 0.5,
            source_id=f"seg-{i}",
        )
        for i in range(count)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", default="100,1000,2000")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = []
    for raw in args.segments.split(","):
        count = int(raw)
        start = time.perf_counter()
        report = build_report_from_segments(build_segments(count))
        elapsed = time.perf_counter() - start
        rows.append(
            {
                "segments": count,
                "elapsed_seconds": round(elapsed, 4),
                "rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "status": report.final_status.value,
            }
        )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
