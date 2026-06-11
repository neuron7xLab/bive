from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "src" / "bive" / "resources" / "science_registry.json"
DOC = ROOT / "docs" / "BIBLIOGRAPHY.md"
ARTIFACT = ROOT / "artifacts" / "verification" / "BIBLIOGRAPHY_VALIDATION.json"
MIN_REFERENCES = 14
REQUIRED_DOMAINS = {
    "behavioral deception research",
    "psychophysiology",
    "cognitive science / judgment",
    "affective computing / HCI",
    "AI risk management",
    "secure software engineering",
    "API security",
    "accessibility / HCI",
    "neurophysiology / predictive processing",
    "multimodal machine learning",
    "provenance / data lineage",
    "open-source security automation",
}


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8")
    errors: list[str] = []
    references = data.get("references", [])
    if len(references) < MIN_REFERENCES:
        errors.append(f"references {len(references)} < {MIN_REFERENCES}")
    domains = {str(ref.get("domain")) for ref in references}
    missing_domains = sorted(REQUIRED_DOMAINS - domains)
    if missing_domains:
        errors.append(f"missing domains: {missing_domains}")
    for ref in references:
        ref_id = str(ref.get("id"))
        if ref_id not in doc:
            errors.append(f"docs/BIBLIOGRAPHY.md missing reference id {ref_id}")
        if not str(ref.get("source_url", "")).startswith("https://"):
            errors.append(f"reference {ref_id} missing https source_url")
        boundary = str(ref.get("claim_boundary", "")).lower()
        if "not" not in boundary and "no " not in boundary:
            errors.append(f"reference {ref_id} lacks explicit negative claim boundary")

    if errors:
        raise SystemExit("BIBLIOGRAPHY_FAIL\n" + "\n".join(f"- {e}" for e in errors))
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps(
            {"status": "pass", "references": len(references), "domains": sorted(domains)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("BIBLIOGRAPHY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
