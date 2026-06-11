from __future__ import annotations

from .models import Claim, Hypothesis, ReviewStatus


def build_verification_questions(
    claims: list[Claim], hypotheses: list[Hypothesis], limit: int = 10
) -> tuple[str, ...]:
    questions: list[str] = []
    temporal = [c for c in claims if "temporal" in c.qualifiers]
    absolute = [c for c in claims if "absolute" in c.qualifiers]
    for c in temporal[:3]:
        questions.append(
            f"Can the time anchor in claim `{c.claim_id}` be verified by an independent source?"
        )
    for c in absolute[:3]:
        questions.append(
            f"What evidence would falsify the absolute wording in claim `{c.claim_id}`?"
        )
    for h in hypotheses:
        if h.status in {ReviewStatus.ELEVATED_RISK, ReviewStatus.REVIEW_REQUIRED}:
            questions.append(
                f"What counter-evidence would lower hypothesis `{h.hypothesis_id}` below review threshold?"
            )
    if not questions:
        questions.append(
            "What independent source could confirm the central claim without relying on behavioral cues?"
        )
    return tuple(dict.fromkeys(questions))[:limit]
