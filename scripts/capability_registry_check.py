"""Capability Registry gate (PR-7).

Every capability the product declares (in the machine-readable capability envelope,
``bive.cogveritas.capabilities``) MUST map to a real implementation module, and
every declared hard limit MUST map to an enforcement mechanism that exists. A
capability with no backing code, or a limit with no enforcement, is an unsupported
claim and fails the gate.

Writes ``artifacts/verification/CAPABILITY_REGISTRY.json``; emits
``CAPABILITY_REGISTRY_PASS``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "verification" / "CAPABILITY_REGISTRY.json"
sys.path.insert(0, str(ROOT / "src"))

from bive.cogveritas.capabilities import capabilities_envelope  # noqa: E402

_COG = "src/bive/cogveritas"
# Declared capability id -> backing implementation module that must exist.
_BACKING = {
    "verifiability": f"{_COG}/verifiability_tagger.py",
    "corroboration_worklist": f"{_COG}/worklist.py",
    "interview_questions": f"{_COG}/interview.py",
    "timeline": f"{_COG}/timeline.py",
    "inconsistencies": f"{_COG}/timeline.py",
    "cross_witness": f"{_COG}/witness.py",
    "entity_index": f"{_COG}/entities.py",
    "reality_monitoring": f"{_COG}/reality_monitoring.py",
    "case_tracking": f"{_COG}/service.py",
    "ingestion": f"{_COG}/ingest.py",
    "dossier": f"{_COG}/dossier.py",
    "integrity": f"{_COG}/integrity.py",
}
# Hard-limit keyword -> enforcement mechanism file.
_LIMIT_ENFORCEMENT = {
    "verdict": f"{_COG}/output_contract.py",
    "lie detector": "scripts/product_claim_audit.py",
    "probability": f"{_COG}/output_contract.py",
    "human": f"{_COG}/capabilities.py",
}


def check() -> tuple[dict[str, object], list[str]]:
    env = capabilities_envelope()
    problems: list[str] = []
    registry: list[dict[str, object]] = []

    for cap in env.get("capabilities", []):
        cid = str(cap.get("id", ""))
        backing = _BACKING.get(cid)
        exists = bool(backing) and (ROOT / backing).is_file() if backing else False
        registry.append({"id": cid, "backing": backing or "", "backed": exists})
        if backing is None:
            problems.append(f"declared capability has no registered backing module: {cid!r}")
        elif not exists:
            problems.append(f"capability {cid!r} backing module missing: {backing}")

    limits = [str(x) for x in env.get("hard_limits", [])]
    if not limits:
        problems.append("capability envelope declares no hard limits")
    for keyword, mechanism in _LIMIT_ENFORCEMENT.items():
        cited = any(keyword in limit.lower() for limit in limits)
        if cited and not (ROOT / mechanism).is_file():
            problems.append(f"hard-limit {keyword!r} enforcement mechanism missing: {mechanism}")

    if not env.get("human_in_the_loop"):
        problems.append("capability envelope does not assert human_in_the_loop")

    artifact = {
        "engine": env.get("engine"),
        "capabilities": registry,
        "capability_count": len(registry),
        "hard_limit_count": len(limits),
        "human_in_the_loop": bool(env.get("human_in_the_loop")),
        "problems": problems,
        "status": "PASS" if not problems else "FAIL",
    }
    return artifact, problems


def main() -> int:
    artifact, problems = check()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if problems:
        for p in problems:
            print(f"CAPABILITY_REGISTRY_ISSUE {p}")
        print(f"CAPABILITY_REGISTRY_FAIL {len(problems)} issue(s)")
        return 1
    print(f"CAPABILITY_REGISTRY_PASS {artifact['capability_count']} capabilities backed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
