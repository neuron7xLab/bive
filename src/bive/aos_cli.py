from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from .aos import (
    ScoreBreakdown,
    build_execution_contract,
    compile_intent,
    kernel_status,
    score_output,
)
from .cognitive_control import orchestrate_request
from .neurocognitive import neurocognitive_protocol_status
from .product import product_readiness_status


def cmd_status(args: argparse.Namespace) -> int:
    print(json.dumps(kernel_status(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_compile(args: argparse.Namespace) -> int:
    intent = compile_intent(args.request)
    contract = build_execution_contract(intent)
    print(
        json.dumps(
            {"intent": intent.to_dict(), "execution_contract": contract.to_dict()},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_control(args: argparse.Namespace) -> int:
    request = " ".join(args.request).strip()
    print(json.dumps(orchestrate_request(request).to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_neurocognitive(args: argparse.Namespace) -> int:
    print(json.dumps(neurocognitive_protocol_status(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_product(args: argparse.Namespace) -> int:
    print(json.dumps(product_readiness_status(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("AOS_ERROR score input must be object", file=sys.stderr)
        return 2
    required = {
        "intent_fidelity",
        "operational_specificity",
        "contract_completeness",
        "verification_strength",
        "failure_coverage",
        "context_efficiency",
        "safety_boundary",
        "reuse_value",
        "production_fit",
        "falsifiability",
    }
    missing = sorted(required - set(data))
    if missing:
        print(f"AOS_ERROR missing metrics: {', '.join(missing)}", file=sys.stderr)
        return 2
    scores = cast(ScoreBreakdown, {name: int(data[name]) for name in required})
    result = score_output(scores)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] != "revise" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bive-aos")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status", help="Print AOS kernel runtime status.")
    status.set_defaults(func=cmd_status)
    compile_cmd = sub.add_parser("compile", help="Compile a request into intent and contract.")
    compile_cmd.add_argument("request")
    compile_cmd.set_defaults(func=cmd_compile)
    control = sub.add_parser("control", help="Route a request through the cognitive control plane.")
    control.add_argument("request", nargs="+")
    control.set_defaults(func=cmd_control)
    neuro = sub.add_parser("neurocognitive", help="Print neurocognitive operational protocol status.")
    neuro.set_defaults(func=cmd_neurocognitive)
    product = sub.add_parser("product", help="Print industrial product readiness status.")
    product.set_defaults(func=cmd_product)
    score = sub.add_parser("score", help="Score prompt output metrics JSON.")
    score.add_argument("--input", required=True)
    score.set_defaults(func=cmd_score)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
