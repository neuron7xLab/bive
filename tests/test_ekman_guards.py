from __future__ import annotations

from bive.benchmark import run_othello_benchmark
from bive.fusion import NON_ESCALATING_FAMILIES, status_from
from bive.ingest import TranscriptSegment
from bive.models import ReviewStatus
from bive.report import build_report_from_segments


def _status(*texts: str) -> str:
    segments = [TranscriptSegment("s", t, i, i + 1) for i, t in enumerate(texts)]
    return build_report_from_segments(segments).final_status.value


def test_othello_error_affect_only_does_not_escalate() -> None:
    # Aroused, content-free, and it invites verification — must not escalate.
    status = _status(
        "Можливо, я говорю плутано, бо дуже хвилююся, але перевірте всі документи.",
        "Мені страшно і тривожно, звіряйте кожну деталь будь ласка.",
    )
    assert status not in ("review_required", "elevated_risk")


def test_othello_note_recorded_on_hypothesis() -> None:
    # A long, purely negative-emotion account (a supporting affect cue) with no
    # substantive content — the Othello guard must fire and stay non-elevated.
    affect_only = (
        "I am afraid and scared, but the fear is real. I feel dread and worry, but I am not "
        "sure. This threat frightens me, but I endure it. The danger and the mess make me "
        "anxious, but I stay. I feel awful and sad, but I still speak here."
    )
    report = build_report_from_segments([TranscriptSegment("s", affect_only, 0, 1)])
    notes = " ".join(a for h in report.hypotheses for a in h.alternative_explanations)
    assert "othello_error_guard" in notes
    assert report.final_status.value not in ("review_required", "elevated_risk")


def test_contradiction_still_escalates() -> None:
    assert _status("I never received that money.", "I received that money later.") == "review_required"


def test_no_single_sign_requires_family_diversity() -> None:
    # A single affect family with a high score still must not reach review.
    high_affect_only = status_from(0.9, 0.3, 5, frozenset({"affect"}))
    assert high_affect_only == ReviewStatus.LOW_RISK
    # Content alone may escalate; two distinct substantive families may escalate.
    assert status_from(0.6, 0.3, 3, frozenset({"content"})) == ReviewStatus.REVIEW_REQUIRED
    assert status_from(0.6, 0.3, 3, frozenset({"manipulation", "framing"})) == ReviewStatus.REVIEW_REQUIRED
    assert status_from(0.6, 0.3, 3, frozenset({"style"})) == ReviewStatus.LOW_RISK


def test_non_escalating_families_are_arousal_context_mitigation() -> None:
    assert NON_ESCALATING_FAMILIES == frozenset({"affect", "context", "mitigation"})


def test_othello_benchmark_specificity_is_perfect() -> None:
    result = run_othello_benchmark()
    assert result["specificity"] == 1.0
    assert result["n"] == 6


def test_report_carries_ekman_limitations() -> None:
    report = build_report_from_segments([TranscriptSegment("s", "I received the money.", 0, 1)])
    joined = " ".join(report.limitations).lower()
    assert "othello" in joined
    assert "brokaw" in joined
