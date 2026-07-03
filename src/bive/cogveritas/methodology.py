"""COGVERITAS methodology contract — the *why* behind the no-verdict posture.

The system refuses person-level verdicts. That refusal is not caution; it is an
empirically forced position. This module exposes the evidence as a structured,
provenanced contract so the honesty is machine-discoverable — a client (or the
UI banner) can answer "why no verdict?" without a human reading the docs.

Every figure here is sourced verbatim from ``docs/EMPIRICAL_VALIDATION.md`` and
the reproducible pipeline in ``research/cogveritas/``; nothing is invented at
runtime. The text deliberately avoids the forbidden person-level judgment
substrings so this surface is itself clean under the no-verdict scan.
"""

from __future__ import annotations

from typing import Any

# Provenance for the whole contract: the numbers below are not computed here,
# they are transcribed from a validated, reproducible artifact.
_PROVENANCE = "docs/EMPIRICAL_VALIDATION.md; research/cogveritas/ (fetch_data.sh + evaluate.py)"

# The empirical law, with the specific regimes that force it. AUC/ECE values are
# copied from the validation table; each row reads as a plain-language finding.
_FINDINGS: tuple[dict[str, str], ...] = (
    {
        "regime": "in-domain (Ott Deceptive Opinion Spam, 5-fold)",
        "roc_auc": "0.75 [0.73-0.77]",
        "ece": "0.024",
        "reads": "discrimination is real but modest, and calibrated in-domain",
    },
    {
        "regime": "cross-corpus (Ott -> Diplomacy)",
        "roc_auc": "0.61",
        "ece": "0.57",
        "reads": "calibration collapses off the training distribution",
    },
    {
        "regime": "Real-Life Trial (121 courtroom transcripts, real high-stakes)",
        "roc_auc": "0.562 [0.46-0.67]",
        "ece": "n/a",
        "reads": "confidence interval straddles chance",
    },
    {
        "regime": "Op-Spam -> Real-Life Trial transfer",
        "roc_auc": "0.548",
        "ece": "n/a",
        "reads": "chance; nothing transfers from low-stakes reviews to real deception",
    },
    {
        "regime": "TF-IDF bag-of-words control (in-domain -> cross-corpus)",
        "roc_auc": "0.955 -> 0.510",
        "ece": "0.157",
        "reads": "a high headline that collapses to chance is lexical leakage, not signal",
    },
)

# What replicates this — the independent literature the negative result reproduces.
_REPLICATES: tuple[str, str] = (
    "DePaulo et al. 2003 — mean verbal cue effect size d = 0.10",
    "Bond & DePaulo 2006 — 54% human accuracy, barely above chance",
)


def methodology_contract() -> dict[str, Any]:
    """The structured epistemic contract behind the no-verdict invariant."""
    return {
        "posture": (
            "COGVERITAS emits no person-level verdict. It maps an account to "
            "externally checkable claims and generates corroboration questions "
            "for human review — it never decides whether a person told the truth."
        ),
        "empirical_law": (
            "Passive verbal deception detection does not work on real "
            "high-stakes deception. On the Real-Life Trial corpus the interpretable "
            "model's confidence interval straddles chance and the high-accuracy "
            "black box collapses to chance. The no-verdict invariant is therefore "
            "the only defensible position, not a stylistic choice."
        ),
        "findings": [dict(f) for f in _FINDINGS],
        "replicates": list(_REPLICATES),
        "calibration_policy": (
            "Calibrated probabilities are defensible only in-domain (ECE below "
            "0.10). Off the training distribution calibration collapses, so the "
            "system surfaces ordinal review flags and never probabilities — an "
            "empirically forced rule enforced by the output contract."
        ),
        "what_it_does_instead": (
            "A human-review evidence assistant: cited construct flags (Verifiability "
            "Approach, Reality Monitoring, Newman-Pennebaker) and concrete "
            "corroboration questions that route a reviewer to external facts."
        ),
        "boundary": (
            "No person-level deception, culpability, intent, diagnosis, or legal "
            "conclusion is ever produced as a machine output."
        ),
        "provenance": _PROVENANCE,
        "reproduce": "cd research/cogveritas && ./fetch_data.sh && python evaluate.py",
    }
