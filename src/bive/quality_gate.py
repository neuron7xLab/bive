from __future__ import annotations

from dataclasses import dataclass

from .models import VerificationReport
from .pseudoscience_guard import scan_text_for_pseudo


@dataclass(frozen=True)
class GateIssue:
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class GateResult:
    passed: bool
    issues: tuple[GateIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return {"passed": self.passed, "issues": [i.to_dict() for i in self.issues]}


def assess_report(report: VerificationReport) -> GateResult:
    issues: list[GateIssue] = []
    joined = "\n".join([report.final_assessment, *report.limitations, *report.missing_evidence])
    pseudo_hits = scan_text_for_pseudo(joined)
    if pseudo_hits:
        issues.append(GateIssue("PSEUDO_VERDICT_LANGUAGE", f"forbidden terms: {pseudo_hits}"))
    if not report.limitations:
        issues.append(GateIssue("MISSING_LIMITATIONS", "report must state limitations"))
    if not report.verification_questions:
        issues.append(
            GateIssue(
                "MISSING_VERIFICATION_QUESTIONS", "report must propose next verification questions"
            )
        )
    for h in report.hypotheses:
        if h.score >= 0.72 and not h.alternative_explanations:
            issues.append(
                GateIssue("NO_ALTERNATIVES", f"{h.hypothesis_id} lacks alternative explanations")
            )
        if h.score >= 0.72 and h.uncertainty > 0.7:
            issues.append(
                GateIssue(
                    "UNCALIBRATED_ESCALATION", f"{h.hypothesis_id} high score with high uncertainty"
                )
            )
    return GateResult(not issues, tuple(issues))
