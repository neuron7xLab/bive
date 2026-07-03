"""Product Claim Audit — the gate that makes unsupported claims impossible."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import product_claim_audit as pca  # noqa: E402  (needs scripts/ on sys.path first)


@pytest.mark.parametrize(
    "text",
    [
        "COGVERITAS is a lie detector.",
        "It detects deception in testimony.",
        "Our model identifies liars automatically.",
        "The system is 95% accurate on real cases.",
        "We guarantee reliable truth detection.",
        "Fully reliable across every domain.",
        "Outputs a deception probability per statement.",
    ],
)
def test_asserted_overclaims_are_caught(text: str) -> None:
    assert pca.scan_text(text), f"overclaim not caught: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "COGVERITAS is not a lie detector.",
        "It does not detect deception; it structures claims.",
        "This is not a truth detection system.",
        "не детектор брехні — лише структурує твердження",
        "BIVE is not:\n- a lie detector;\n- a truth machine;",
        "Bond & DePaulo 2006 (54% accuracy) — the human baseline.",
        "No verdict is ever produced; verdict: null.",
    ],
)
def test_disclaimed_or_cited_language_is_allowed(text: str) -> None:
    assert pca.scan_text(text) == [], f"false positive on: {text!r}"


def test_live_repository_has_no_overclaims() -> None:
    # Regression guard: the shipped product surfaces must stay clean.
    violations, scanned = pca.audit()
    assert scanned, "no surfaces were scanned"
    assert violations == [], f"overclaims present: {violations}"


def test_percent_without_year_is_flagged_but_citation_is_not() -> None:
    assert pca.scan_text("achieves 98% accuracy")  # bare product claim
    assert pca.scan_text("Smith 2019 reported 98% accuracy") == []  # citation
