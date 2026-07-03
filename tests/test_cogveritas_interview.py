"""Interview question generation — elicit checkable detail, never accuse."""

from __future__ import annotations

from bive.cogveritas.interview import interview_questions
from bive.cogveritas.output_contract import FORBIDDEN_JUDGMENT_STRINGS
from bive.cogveritas.service import analyze_verifiability
from bive.cogveritas.verifiability_tagger import analyze


def _q(text: str) -> list[dict[str, object]]:
    _, claims = analyze(text)
    return interview_questions(claims)


def test_unverifiable_claim_gets_elicit_question() -> None:
    qs = _q("Я думаю, що все було добре того разу насправді.")
    assert qs
    assert any("перевірюван" in str(q["question"]) for q in qs)


def test_missing_time_is_probed() -> None:
    qs = _q("Я передав Петру гроші біля станції.")
    assert any("час" in str(q["question"]) for q in qs)


def test_well_anchored_claim_needs_no_question() -> None:
    # time + place + entity present -> nothing to elicit.
    qs = _q("Петро прийшов о 14:30 на вулиця Банкова.")
    assert qs == []


def test_service_exposes_interview_questions_verdict_null() -> None:
    out = analyze_verifiability("Я комусь щось віддав тоді.")
    assert out.interview_questions
    for iq in out.interview_questions:
        assert iq.claim_id and iq.question
    assert out.verdict is None


def test_interview_questions_carry_no_judgment_framing() -> None:
    import re

    out = analyze_verifiability("Він точно щось приховував, я впевнений.")
    for iq in out.interview_questions:
        framing = re.sub(r"«[^»]*»", "«…»", iq.question).lower()
        assert all(s not in framing for s in FORBIDDEN_JUDGMENT_STRINGS)
