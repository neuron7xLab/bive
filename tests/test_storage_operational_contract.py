from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from bive.ingest import TranscriptSegment
from bive.report import build_report_from_segments
from bive.storage import ReportStore


def test_storage_exposes_schema_version(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    assert store.schema_version() == 1
    assert store.stats()["schema_version"] == 1


def test_storage_handles_concurrent_report_writes(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    base = build_report_from_segments(
        [TranscriptSegment(speaker="A", text="I never changed this.")]
    )

    def write_one(index: int) -> None:
        store.save(replace(base, report_id=f"bive-report-{index:04d}"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(write_one, range(24)))

    stats = store.stats()
    assert stats["report_count"] == 24
    assert stats["audit_event_count"] == 24
