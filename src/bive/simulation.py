from __future__ import annotations

from dataclasses import dataclass

from .ingest import TranscriptSegment
from .report import build_report_from_segments


@dataclass(frozen=True)
class SimulationSummary:
    scenario: str
    status: str
    max_score: float
    mean_uncertainty: float
    event_count: int

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "scenario": self.scenario,
            "status": self.status,
            "max_score": self.max_score,
            "mean_uncertainty": self.mean_uncertainty,
            "event_count": self.event_count,
        }


def scenario_segments() -> dict[str, list[TranscriptSegment]]:
    return {
        "calm_verified": [
            TranscriptSegment("s1", "Ось документи. Перевірте час, суму і людей у журналі.", 0, 4)
        ],
        "pressure_no_check": [
            TranscriptSegment(
                "s1", "Повір мені. Не треба перевіряти. Очевидно всі знають, що я правий.", 0, 5
            )
        ],
        "temporal_contradiction": [
            TranscriptSegment("s1", "Я не підписував акт вчора.", 0, 2),
            TranscriptSegment("s1", "Вчора я підписував акт після зустрічі.", 3, 5),
        ],
        "high_entropy_noise": [
            TranscriptSegment("s1", "Може, типу, не знаю, мабуть, воно якось там сталося.", 0, 3),
            TranscriptSegment("s1", "Але перевіряйте всі дані, я не проти.", 4, 7),
        ],
    }


def run_simulation() -> list[SimulationSummary]:
    out: list[SimulationSummary] = []
    for name, segments in scenario_segments().items():
        report = build_report_from_segments(segments, subject_scope=name)
        max_score = max((h.score for h in report.hypotheses), default=0.0)
        mean_uncertainty = sum(h.uncertainty for h in report.hypotheses) / max(
            1, len(report.hypotheses)
        )
        out.append(
            SimulationSummary(
                scenario=name,
                status=report.final_status.value,
                max_score=round(max_score, 4),
                mean_uncertainty=round(mean_uncertainty, 4),
                event_count=len(report.evidence_events),
            )
        )
    return out
