"""External Replication Package gate (PR-6).

Validates that an independent party could reproduce the empirical claims from public
data: the replication assets exist, the replication guide documents the exact steps
and references those scripts, and the frozen result artifact is present as the
reference. Emits ``EXTERNAL_REPLICATION_READY``; exits non-zero if the package is
incomplete.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "cogveritas"
GUIDE = RESEARCH / "REPLICATION.md"
PUBLIC_GUIDE = ROOT / "docs" / "methodology" / "EXTERNAL_REPLICATION_GUIDE.md"
OUT = ROOT / "artifacts" / "verification" / "EXTERNAL_REPLICATION_READINESS.json"

# Assets an external replicator needs (relative to research/cogveritas/).
_REQUIRED_ASSETS = (
    "fetch_data.sh",
    "features.py",
    "evaluate.py",
    "leakage_audit.py",
    "rlt_transfer.py",
    "phase0_results.json",
    "PHASE0_REPORT.md",
)
# The guide must reference the runnable entry points.
_REQUIRED_STEPS = ("fetch_data.sh", "evaluate.py", "leakage_audit.py", "rlt_transfer.py")
# Runnable code assets that must contain a real implementation, not a stub — file
# existence alone lets a 0-byte / NotImplementedError placeholder claim readiness.
_PY_ENTRYPOINTS = ("features.py", "evaluate.py", "leakage_audit.py", "rlt_transfer.py")
_SH_ENTRYPOINTS = ("fetch_data.sh",)
_MIN_CODE_LINES = 8


def _code_line_count(src: str) -> int:
    return sum(1 for line in src.splitlines() if line.strip() and not line.strip().startswith("#"))


def _raises_not_implemented(node: ast.Raise) -> bool:
    exc: ast.expr | None = node.exc
    if isinstance(exc, ast.Call):
        exc = exc.func
    if isinstance(exc, ast.Name):
        return exc.id in {"NotImplementedError", "NotImplemented"}
    if isinstance(exc, ast.Attribute):
        return exc.attr in {"NotImplementedError", "NotImplemented"}
    return False


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
        return False  # a real statement -> not a stub
    return True


def _py_stub_reason(src: str) -> str | None:
    if _code_line_count(src) < _MIN_CODE_LINES:
        return "too small to be a real implementation"
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return f"does not parse ({exc.msg})"
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not funcs:
        return "defines no functions (placeholder)"
    if all(_is_stub_body(fn) for fn in funcs):
        return "every function is a stub (pass/.../NotImplementedError)"
    return None


def _sh_stub_reason(src: str) -> str | None:
    commands = [
        line for line in src.splitlines()
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("#!")
    ]
    if len(commands) < 3:
        return "too small to be a real fetch script"
    return None


def check() -> list[str]:
    problems: list[str] = []
    for asset in _REQUIRED_ASSETS:
        if not (RESEARCH / asset).is_file():
            problems.append(f"missing replication asset: research/cogveritas/{asset}")
    # Existence is not enough: the runnable assets must carry a real implementation.
    for asset in _PY_ENTRYPOINTS:
        path = RESEARCH / asset
        if path.is_file():
            reason = _py_stub_reason(path.read_text(encoding="utf-8"))
            if reason:
                problems.append(f"replication asset is not runnable: {asset} — {reason}")
    for asset in _SH_ENTRYPOINTS:
        path = RESEARCH / asset
        if path.is_file():
            reason = _sh_stub_reason(path.read_text(encoding="utf-8"))
            if reason:
                problems.append(f"replication asset is not runnable: {asset} — {reason}")
    if not GUIDE.is_file():
        problems.append("missing replication guide: research/cogveritas/REPLICATION.md")
        return problems
    guide = GUIDE.read_text(encoding="utf-8")
    for step in _REQUIRED_STEPS:
        if step not in guide:
            problems.append(f"replication guide omits step referencing {step!r}")
    # The guide must anchor to the frozen reference and state an expected number.
    if "phase0_results.json" not in guide:
        problems.append("replication guide does not anchor to the frozen phase0_results.json")
    if "0.75" not in guide and "0.562" not in guide:
        problems.append("replication guide states no expected reproduction figure")
    # The public-facing guide must exist and state fail-closed-on-unavailable-data.
    if not PUBLIC_GUIDE.is_file():
        problems.append("missing public guide: docs/methodology/EXTERNAL_REPLICATION_GUIDE.md")
    else:
        pub = PUBLIC_GUIDE.read_text(encoding="utf-8").lower()
        if "blocked" not in pub and "fail-closed" not in pub:
            problems.append("public guide does not state fail-closed on unavailable data")
    return problems


def main() -> int:
    problems = check()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "guide": "docs/methodology/EXTERNAL_REPLICATION_GUIDE.md",
                "assets": list(_REQUIRED_ASSETS),
                "externally_replicated": False,
                "readiness": "ready" if not problems else "incomplete",
                "problems": problems,
                "status": "PASS" if not problems else "FAIL",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if problems:
        for p in problems:
            print(f"EXTERNAL_REPLICATION_ISSUE {p}")
        print(f"EXTERNAL_REPLICATION_FAIL {len(problems)} issue(s)")
        return 1
    print("EXTERNAL_REPLICATION_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
