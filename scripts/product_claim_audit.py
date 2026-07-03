"""Product Claim Audit — make unsupported claims impossible (fail-closed).

Implements PR-4 / §12 of the COGVERITAS Institutional Level-Up Specification: scan
every public surface (README, docs, UI copy, OpenAPI, CLI help, capability/
methodology/dossier text) and BLOCK the release if the product language overclaims
beyond the evidence boundary.

The rule the spec encodes:

    A higher score is not earned by adding features.
    A higher score is earned by making unsupported claims impossible.

An overclaim is an *asserted* capability the evidence does not support — a lie
detector, a deception probability, an unqualified reliability/accuracy claim,
cross-domain transfer without an artifact. A *disclaimed* mention (negated: "not a
lie detector", "does not detect deception", "не детектор брехні") is allowed and
required — surfacing the limit is the whole point.

Emits ``PRODUCT_CLAIM_AUDIT_PASS`` and writes ``artifacts/verification/
PRODUCT_CLAIM_AUDIT.json``; exits non-zero on any un-disclaimed overclaim.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "verification" / "PRODUCT_CLAIM_AUDIT.json"

# Public surfaces the audit governs (existing paths only).
_SURFACE_FILES = (
    "README.md",
    "docs/openapi.json",
    "src/bive/web/index.html",
    "src/bive/web/static/app.js",
    "src/bive/cli.py",
    "src/bive/cogveritas/capabilities.py",
    "src/bive/cogveritas/methodology.py",
    "src/bive/cogveritas/dossier.py",
)
_SURFACE_DIRS = ("docs",)
# Files that necessarily *quote* overclaims as illustrative examples (the policy
# itself, and the spec it implements) — governance text, not product claims.
_EXEMPT = {
    "docs/methodology/PRODUCT_CLAIM_POLICY.md",
    "docs/methodology/COGVERITAS_OPENAI_STYLE_LEVEL_UP_SPEC.md",
}

# Overclaim patterns: an *asserted* capability the evidence does not support.
# Each is only a violation when NOT in a disclaimer/negated context (see below).
_OVERCLAIM = [
    ("lie_detector", re.compile(r"\blie[\s-]?detector\b", re.I)),
    ("detects_deception", re.compile(r"\bdetect(?:s|ing|ion)?\b[^.\n]{0,20}\b(?:lie|lies|deception|liar)", re.I)),
    ("identifies_liars", re.compile(r"\bidentif(?:y|ies|ying)\b[^.\n]{0,20}\b(?:liar|liars|deception|lies)", re.I)),
    ("truth_detection", re.compile(r"\btruth[\s-]?detection\b", re.I)),
    ("percent_accuracy", re.compile(r"\b\d{2,3}\s?%\s*(?:accura|reliab|correct)", re.I)),
    ("guarantee", re.compile(r"\bguarantee(?:s|d)?\b", re.I)),
    ("proven_detect", re.compile(r"\bproven\b[^.\n]{0,25}\b(?:detect|deception|truth|accura)", re.I)),
    ("unqualified_reliable", re.compile(r"\b(?:highly|fully|100%)\s+(?:reliable|accurate)\b", re.I)),
    ("deception_probability", re.compile(r"\b(?:deception|lie|truth)\s+(?:probability|score|likelihood)\b", re.I)),
]

# Disclaimer / negation markers. If any appears within the window before a match
# (or anywhere on the line), the mention is a *limit statement*, not a claim.
_NEG_WINDOW = 48
_NEGATORS = (
    "not ", "no ", "n't", "never", "cannot", "can't", "does not", "do not", "isn't",
    "is not", "are not", "without", "refuse", "неможлив", "не ", "ні ", "не є",
    "жодн", "не детектор", "no verdict", "not a lie", "never a", "не визначає",
    "not claim", "does not claim", "not a truth", "structurally null", "verdict: null",
    "по замыслу", "за задумом", "not a deception",
)


_YEAR = re.compile(r"\b(?:18|19|20)\d{2}\b")


def _is_disclaimed(prev_context: str, line: str, start: int) -> bool:
    lowered = line.lower()
    window = lowered[max(0, start - _NEG_WINDOW) : start]
    if any(neg in window for neg in _NEGATORS):
        return True
    # A negation on a nearby preceding line (e.g. a list under "BIVE is not:").
    if any(neg in prev_context.lower() for neg in ("is not", "are not", "not:", "не є", "не:", "must not")):
        return True
    # Whole-line disclaimer context (e.g. a limits sentence quoting the term).
    return any(neg in lowered for neg in ("not a lie", "не детектор", "no verdict", "does not detect", "не визначає"))


def _is_citation(line: str, start: int) -> bool:
    """A percentage next to a 4-digit year is a scholarly citation, not a claim."""
    around = line[max(0, start - 24) : start + 8]
    return bool(_YEAR.search(around))


def _iter_surfaces() -> list[Path]:
    seen: dict[Path, None] = {}
    for rel in _SURFACE_FILES:
        p = ROOT / rel
        if p.is_file():
            seen[p] = None
    for d in _SURFACE_DIRS:
        for p in sorted((ROOT / d).rglob("*")):
            if p.is_file() and p.suffix in {".md", ".json", ".txt"}:
                seen[p] = None
    return list(seen)


def scan_text(text: str) -> list[dict[str, object]]:
    """Un-disclaimed overclaims in a text blob: [{line, kind, match}]."""
    found: list[dict[str, object]] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        prev_context = "\n".join(lines[max(0, lineno - 3) : lineno - 1])
        for kind, pattern in _OVERCLAIM:
            for m in pattern.finditer(line):
                if _is_disclaimed(prev_context, line, m.start()):
                    continue
                if kind == "percent_accuracy" and _is_citation(line, m.start()):
                    continue
                found.append({"line": lineno, "kind": kind, "match": m.group(0).strip()[:80]})
    return found


def audit() -> tuple[list[dict[str, object]], list[str]]:
    """Return (violations, scanned surface paths)."""
    violations: list[dict[str, object]] = []
    scanned: list[str] = []
    for path in _iter_surfaces():
        rel = str(path.relative_to(ROOT))
        if rel in _EXEMPT:
            continue
        scanned.append(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for hit in scan_text(text):
            violations.append({"surface": rel, **hit})
    violations.sort(key=lambda v: (str(v["surface"]), str(v["line"]).rjust(9, "0"), str(v["kind"])))
    return violations, sorted(scanned)


def main() -> int:
    violations, scanned = audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "policy": "docs/methodology/PRODUCT_CLAIM_POLICY.md",
                "surfaces_scanned": len(scanned),
                "surfaces": scanned,
                "violations": violations,
                "status": "PASS" if not violations else "FAIL",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if violations:
        for v in violations:
            print(f"OVERCLAIM {v['surface']}:{v['line']} [{v['kind']}] {v['match']!r}")
        print(f"PRODUCT_CLAIM_AUDIT_FAIL {len(violations)} unsupported claim(s)")
        return 1
    print(f"PRODUCT_CLAIM_AUDIT_PASS scanned {len(scanned)} surfaces, 0 overclaims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
