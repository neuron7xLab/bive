from __future__ import annotations

from .models import VerificationReport

REQUIRED_REPORT_KEYS = {
    "report_id",
    "created_at",
    "subject_scope",
    "input_summary",
    "claims",
    "signals",
    "evidence_events",
    "hypotheses",
    "final_status",
    "final_assessment",
    "limitations",
    "missing_evidence",
    "verification_questions",
    "policy_invariants",
}

FORBIDDEN_VERDICT_TERMS = {
    "is lying",
    "is a liar",
    "брехун",
    "лжец",
    "винен",
    "guilty",
}


def validate_report_dict(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_REPORT_KEYS - set(data.keys())
    if missing:
        errors.append(f"missing required keys: {sorted(missing)}")
    assessment = str(data.get("final_assessment", "")).lower()
    for term in FORBIDDEN_VERDICT_TERMS:
        if term in assessment:
            errors.append(f"forbidden person-level verdict term in final_assessment: {term}")
    hypotheses = data.get("hypotheses", [])
    if isinstance(hypotheses, list):
        for idx, h in enumerate(hypotheses):
            if not isinstance(h, dict):
                errors.append(f"hypothesis {idx} must be object")
                continue
            score = h.get("score")
            uncertainty = h.get("uncertainty")
            if not isinstance(score, (float, int)) or not 0 <= float(score) <= 1:
                errors.append(f"hypothesis {idx} score must be in [0,1]")
            if not isinstance(uncertainty, (float, int)) or not 0 <= float(uncertainty) <= 1:
                errors.append(f"hypothesis {idx} uncertainty must be in [0,1]")
            if h.get("status") in {"elevated_risk", "review_required"} and not h.get(
                "alternative_explanations"
            ):
                errors.append(f"hypothesis {idx} requires alternative_explanations")
    else:
        errors.append("hypotheses must be a list")
    return errors


def validate_report(report: VerificationReport) -> list[str]:
    return validate_report_dict(report.to_dict())
