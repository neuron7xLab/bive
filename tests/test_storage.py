from bive.pipeline import analyze_transcript_payload
from bive.storage import ReportStore


def test_report_store_roundtrip(tmp_path) -> None:
    store = ReportStore(tmp_path / "bive.sqlite3")
    report = analyze_transcript_payload(
        {"segments": [{"speaker": "x", "text": "Я ніколи цього не робив."}]}
    )
    store.save(report)
    loaded = store.get(report.report_id)
    assert loaded is not None
    assert loaded.report_id == report.report_id
    assert len(store.list()) == 1
