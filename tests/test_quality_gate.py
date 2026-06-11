import pytest

from bive.ingest import TranscriptSegment
from bive.pseudoscience_guard import assert_no_pseudoscience
from bive.quality_gate import assess_report
from bive.report import build_report_from_segments


def test_quality_gate_accepts_conservative_report():
    report = build_report_from_segments(
        [TranscriptSegment("s", "Повір мені, не треба перевіряти.")]
    )
    result = assess_report(report)
    assert result.passed


def test_pseudoscience_guard_rejects_forbidden_verdict():
    with pytest.raises(ValueError):
        assert_no_pseudoscience("ця людина точно бреше 100%")
