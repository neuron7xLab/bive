from __future__ import annotations

from dataclasses import dataclass

from .ingest import TranscriptSegment
from .report import build_report_from_segments


@dataclass(frozen=True)
class RedTeamCase:
    case_id: str
    description: str
    segments: tuple[TranscriptSegment, ...]
    expected_not_status: str | None = None
    expected_status: str | None = None


@dataclass(frozen=True)
class RedTeamResult:
    case_id: str
    passed: bool
    observed_status: str
    detail: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "observed_status": self.observed_status,
            "detail": self.detail,
        }


def built_in_cases() -> list[RedTeamCase]:
    return [
        RedTeamCase(
            case_id="stress_not_deception",
            description="Stressed language without contradiction must not be escalated to elevated risk.",
            segments=(
                TranscriptSegment(
                    "s1",
                    "Я хвилююсь і можливо говорю плутано, але перевіряйте всі документи.",
                    0,
                    4,
                ),
            ),
            expected_not_status="elevated_risk",
        ),
        RedTeamCase(
            case_id="verification_pressure",
            description="Discouraging verification should require review, not a liar verdict.",
            segments=(
                TranscriptSegment(
                    "s1", "Повір мені, не треба перевіряти, все завжди було чисто.", 0, 4
                ),
            ),
            expected_status="review_required",
        ),
        RedTeamCase(
            case_id="local_tension",
            description="Contradictory local claims should trigger inconsistency review.",
            segments=(
                TranscriptSegment("s1", "Я не був у Києві вчора.", 0, 2),
                TranscriptSegment("s1", "Вчора я був у Києві на зустрічі.", 3, 6),
            ),
            expected_status="review_required",
        ),
    ]


def run_red_team() -> list[RedTeamResult]:
    results: list[RedTeamResult] = []
    for case in built_in_cases():
        report = build_report_from_segments(list(case.segments), subject_scope=case.case_id)
        observed = report.final_status.value
        if case.expected_status is not None:
            passed = observed == case.expected_status
            detail = f"expected {case.expected_status}, observed {observed}"
        elif case.expected_not_status is not None:
            passed = observed != case.expected_not_status
            detail = f"expected not {case.expected_not_status}, observed {observed}"
        else:
            passed = True
            detail = f"observed {observed}"
        results.append(RedTeamResult(case.case_id, passed, observed, detail))
    return results
