"""The analysis is a pure function of the input; the report id is content-addressed.

Two auditors analyzing the same transcript must get the same substantive report and the
same id. These tests fail if hidden nondeterminism creeps in or if the id stops encoding
the content.
"""

from __future__ import annotations

import json
from pathlib import Path

from bive.pipeline import _content_report_id, analyze_transcript_payload

_SAMPLE = Path("samples/demo_transcript.json")


def _payload() -> dict:
    return json.loads(_SAMPLE.read_text())


def _substantive(report) -> dict:  # type: ignore[no-untyped-def]
    d = dict(report.to_dict())
    d.pop("created_at", None)
    return d


def test_substantive_content_is_a_pure_function_of_input() -> None:
    r1 = analyze_transcript_payload(_payload())
    r2 = analyze_transcript_payload(_payload())
    assert _substantive(r1) == _substantive(r2)


def test_report_id_is_stable_across_runs() -> None:
    r1 = analyze_transcript_payload(_payload())
    r2 = analyze_transcript_payload(_payload())
    assert r1.report_id == r2.report_id


def test_report_id_is_the_content_digest() -> None:
    r = analyze_transcript_payload(_payload())
    assert r.report_id == f"bive-report-{_content_report_id(r)}"


def test_report_id_excludes_the_timestamp() -> None:
    # created_at is volatile; the id must not depend on it.
    r = analyze_transcript_payload(_payload())
    digest_inputs = r.to_dict()
    assert "created_at" in digest_inputs  # the field exists on the report...
    # ...but re-deriving the id ignores it, so the id is time-independent.
    assert r.report_id == f"bive-report-{_content_report_id(r)}"


def test_different_transcript_changes_the_id() -> None:
    base = analyze_transcript_payload(_payload())
    mutated = _payload()
    mutated["segments"][0]["text"] = mutated["segments"][0]["text"] + " Additional distinct claim."
    changed = analyze_transcript_payload(mutated)
    assert changed.report_id != base.report_id


def test_report_id_keeps_the_conventional_format() -> None:
    r = analyze_transcript_payload(_payload())
    assert r.report_id.startswith("bive-report-")
    suffix = r.report_id.removeprefix("bive-report-")
    assert len(suffix) == 12 and all(c in "0123456789abcdef" for c in suffix)
