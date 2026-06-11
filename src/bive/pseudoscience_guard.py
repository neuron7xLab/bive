from __future__ import annotations

BANNED_VERDICTS = (
    "liar",
    "брехун",
    "лжец",
    "deception proven",
    "100%",
    "guaranteed lie",
    "точно бреше",
)

REQUIRED_REPORT_FIELDS = (
    "limitations",
    "missing_evidence",
    "verification_questions",
    "policy_invariants",
)


def scan_text_for_pseudo(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in BANNED_VERDICTS if term in lowered]


def assert_no_pseudoscience(text: str) -> None:
    hits = scan_text_for_pseudo(text)
    if hits:
        raise ValueError(f"pseudoscience/verdict language detected: {hits}")
