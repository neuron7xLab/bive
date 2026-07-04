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

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "verification" / "CAPABILITY_REGISTRY.json"
sys.path.insert(0, str(ROOT / "src"))

from bive.cogveritas.capabilities import capabilities_envelope  # noqa: E402

_MIN_CODE_LINES = 8


def _module_stub_reason(src: str) -> str | None:
    """None if the module is a real implementation; a reason if it is a stub.

    File existence is not backing code — a `pass` / `NotImplementedError` placeholder
    is an unsupported capability claim.
    """
    if sum(1 for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#")) < _MIN_CODE_LINES:
        return "too small to be a real implementation"
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return f"does not parse ({exc.msg})"
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    if not funcs and not classes:
        return "defines no functions or classes (placeholder)"
    if funcs and all(_is_stub_body(fn) for fn in funcs):
        return "every function is a stub (pass/.../NotImplementedError)"
    return None


def _is_stub_body(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(
        body[0].value.value, str
    ):
        body = body[1:]  # drop the docstring
    if not body:
        return True
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
            continue
        if isinstance(stmt, ast.Raise) and _raises_not_implemented(stmt):
            continue
        return False
    return True


def _raises_not_implemented(node: ast.Raise) -> bool:
    exc: ast.expr | None = node.exc
    if isinstance(exc, ast.Call):
        exc = exc.func
    if isinstance(exc, ast.Name):
        return exc.id in {"NotImplementedError", "NotImplemented"}
    if isinstance(exc, ast.Attribute):
        return exc.attr in {"NotImplementedError", "NotImplemented"}
    return False

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
        path = (ROOT / backing) if backing else None
        # Backing means a real implementation, not merely that the file exists.
        stub_reason = _module_stub_reason(path.read_text(encoding="utf-8")) if path and path.is_file() else None
        backed = bool(path and path.is_file() and stub_reason is None)
        registry.append({"id": cid, "backing": backing or "", "backed": backed})
        if backing is None:
            problems.append(f"declared capability has no registered backing module: {cid!r}")
        elif not (path and path.is_file()):
            problems.append(f"capability {cid!r} backing module missing: {backing}")
        elif stub_reason:
            problems.append(f"capability {cid!r} backing module is not a real implementation: {backing} — {stub_reason}")

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
