"""Content digest = tamper-evidence for verification reports.

The digest must match the substantive content, ignore the volatile record fields
(report_id, created_at), and break on any change to the analysis.
"""

from __future__ import annotations

import json
from pathlib import Path

from bive.integrity import EXCLUDED_KEYS, content_digest, verify_content_digest
from bive.pipeline import analyze_transcript_payload

_SAMPLE = Path("samples/demo_transcript.json")


def _report() -> dict:
    return analyze_transcript_payload(json.loads(_SAMPLE.read_text())).to_dict()


def test_generated_report_carries_a_valid_digest() -> None:
    payload = _report()
    assert len(payload["content_digest"]) == 64
    assert verify_content_digest(payload)


def test_tampering_any_substantive_field_is_detected() -> None:
    payload = _report()
    for field in ("final_assessment", "final_status", "subject_scope"):
        tampered = dict(payload)
        tampered[field] = str(tampered.get(field, "")) + "_altered"
        assert not verify_content_digest(tampered), f"tampering {field} was not detected"


def test_digest_ignores_volatile_record_fields() -> None:
    payload = _report()
    moved = dict(payload)
    moved["report_id"] = "bive-report-ffffffffffff"
    moved["created_at"] = "2000-01-01T00:00:00Z"
    assert content_digest(moved) == content_digest(payload)
    assert "report_id" in EXCLUDED_KEYS and "created_at" in EXCLUDED_KEYS


def test_same_transcript_same_digest_distinct_ids() -> None:
    # Content-addressed integrity coexists with unique record ids.
    r1 = analyze_transcript_payload(json.loads(_SAMPLE.read_text()))
    r2 = analyze_transcript_payload(json.loads(_SAMPLE.read_text()))
    assert r1.content_digest == r2.content_digest
    assert r1.report_id != r2.report_id


def test_different_transcript_changes_digest() -> None:
    base = _report()
    mutated_payload = json.loads(_SAMPLE.read_text())
    mutated_payload["segments"][0]["text"] += " A materially different claim."
    other = analyze_transcript_payload(mutated_payload).to_dict()
    assert other["content_digest"] != base["content_digest"]


def test_roundtrip_preserves_digest() -> None:
    from bive.models import VerificationReport

    report = analyze_transcript_payload(json.loads(_SAMPLE.read_text()))
    restored = VerificationReport.from_dict(report.to_dict())
    assert restored.content_digest == report.content_digest
    assert verify_content_digest(restored.to_dict())
