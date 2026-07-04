"""Adversarial regression guard for the trust anchor.

Hostile inputs — testimony containing accusations, injected verdicts/probabilities,
forbidden-judgment strings, and degenerate/unicode/injection text — must never make
the system emit a verdict or probability, echo a person-level judgment as its OWN
framing, or crash. Forbidden strings in the INPUT are evidence, not the system's
words; the invariant binds the system's framing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bive.cogveritas.output_contract import _QUOTE_SPAN, FORBIDDEN_JUDGMENT_STRINGS
from bive.cogveritas.service import analyze_verifiability

_CORPUS = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "cogveritas"
    / "validation"
    / "adversarial_corpus.json"
)
_INPUTS: list[str] = json.loads(_CORPUS.read_text(encoding="utf-8"))["inputs"]


@pytest.mark.parametrize("text", _INPUTS)
def test_adversarial_input_never_breaks_the_trust_anchor(text: str) -> None:
    out = analyze_verifiability(text)  # must not raise
    assert out.verdict is None
    assert out.calibrated_probability is None
    framing = " ".join(
        [*out.corroboration_questions, *out.rm_criteria_flagged]
        + [q.question + " " + q.rationale for q in out.interview_questions]
    )
    system_framing = _QUOTE_SPAN.sub("«…»", framing).lower()
    leaked = [s for s in FORBIDDEN_JUDGMENT_STRINGS if s in system_framing]
    assert leaked == [], f"system echoed forbidden judgment as its own framing: {leaked}"


def test_adversarial_corpus_actually_contains_forbidden_strings_as_input() -> None:
    # Guard the guard: the corpus must genuinely exercise the invariant (else it proves
    # nothing). At least one input must contain a forbidden-judgment substring.
    blob = " ".join(_INPUTS).lower()
    assert any(s in blob for s in FORBIDDEN_JUDGMENT_STRINGS)
