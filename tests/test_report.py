import json

from bive.report import build_report_from_transcript, render_markdown, save_report
from bive.validation import validate_report


def test_report_builds_and_validates(tmp_path):
    inp = tmp_path / "input.json"
    inp.write_text(
        json.dumps(
            {"segments": [{"speaker": "A", "text": "Trust me, nobody needs to check this today."}]}
        ),
        encoding="utf-8",
    )
    report = build_report_from_transcript(inp)
    assert report.claims
    assert report.evidence_events
    assert not validate_report(report)


def test_report_serialization(tmp_path):
    inp = tmp_path / "input.json"
    out = tmp_path / "report.json"
    inp.write_text(
        json.dumps(
            {"segments": [{"speaker": "A", "text": "I never said that. I said that today."}]}
        ),
        encoding="utf-8",
    )
    report = build_report_from_transcript(inp)
    save_report(report, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["policy_invariants"]
    assert "liar" not in data["final_assessment"].lower()
    assert "Verification Report" in render_markdown(report)
