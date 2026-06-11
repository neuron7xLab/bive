from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .eval import evaluate_binary
from .quality_gate import assess_report
from .red_team import run_red_team
from .report import build_report_from_transcript, load_report, render_markdown, save_report
from .simulation import run_simulation
from .validation import validate_report_dict


class CliError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def read_json_file(path: str | Path) -> Any:
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CliError("INPUT_NOT_FOUND", str(p)) from exc
    except JSONDecodeError as exc:
        raise CliError("INVALID_JSON", f"{p}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc
    except OSError as exc:
        raise CliError("INPUT_READ_FAILED", f"{p}: {exc}") from exc


def cmd_analyze(args: argparse.Namespace) -> int:
    try:
        report = build_report_from_transcript(args.input)
        save_report(report, args.output)
    except FileNotFoundError as exc:
        raise CliError("INPUT_NOT_FOUND", str(args.input)) from exc
    except JSONDecodeError as exc:
        raise CliError("INVALID_JSON", f"{args.input}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc
    except ValueError as exc:
        raise CliError("INVALID_TRANSCRIPT_SCHEMA", str(exc)) from exc
    except OSError as exc:
        raise CliError("OUTPUT_WRITE_FAILED", str(exc)) from exc
    print(f"WROTE {args.output}")
    print(report.final_assessment)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    data = read_json_file(args.input)
    errors = validate_report_dict(data)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    try:
        report = load_report(args.input)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_markdown(report), encoding="utf-8")
    except FileNotFoundError as exc:
        raise CliError("INPUT_NOT_FOUND", str(args.input)) from exc
    except JSONDecodeError as exc:
        raise CliError("INVALID_JSON", f"{args.input}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc
    except OSError as exc:
        raise CliError("OUTPUT_WRITE_FAILED", str(exc)) from exc
    print(f"WROTE {output}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    data = read_json_file(args.input)
    if not isinstance(data, dict):
        raise CliError("INVALID_EVAL_SCHEMA", "eval input must be an object")
    if "labels" not in data or "predictions" not in data:
        raise CliError("INVALID_EVAL_SCHEMA", "eval input requires labels and predictions")
    try:
        labels = [int(x) for x in data["labels"]]
        predictions = [int(x) for x in data["predictions"]]
    except (TypeError, ValueError) as exc:
        raise CliError(
            "INVALID_EVAL_SCHEMA", "labels and predictions must be integer arrays"
        ) from exc
    try:
        result = evaluate_binary(labels, predictions)
    except ValueError as exc:
        raise CliError("INVALID_EVAL_SCHEMA", str(exc)) from exc
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    rows = [row.to_dict() for row in run_simulation()]
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


def cmd_red_team(args: argparse.Namespace) -> int:
    rows = [row.to_dict() for row in run_red_team()]
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0 if all(row["passed"] for row in rows) else 1


def cmd_gate(args: argparse.Namespace) -> int:
    report = load_report(args.input)
    result = assess_report(report)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bive")
    parser.add_argument("--debug", action="store_true", help="Show raw tracebacks for debugging.")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Build a verification report from transcript JSON.")
    analyze.add_argument("--input", required=True)
    analyze.add_argument("--output", required=True)
    analyze.set_defaults(func=cmd_analyze)

    validate = sub.add_parser("validate", help="Validate report invariants.")
    validate.add_argument("--input", required=True)
    validate.set_defaults(func=cmd_validate)

    render = sub.add_parser("render", help="Render report JSON to Markdown.")
    render.add_argument("--input", required=True)
    render.add_argument("--output", required=True)
    render.set_defaults(func=cmd_render)

    ev = sub.add_parser("eval", help="Evaluate binary predictions from JSON: labels/predictions.")
    ev.add_argument("--input", required=True)
    ev.set_defaults(func=cmd_eval)

    sim = sub.add_parser("simulate", help="Run deterministic entropy/adversarial scenarios.")
    sim.set_defaults(func=cmd_simulate)

    rt = sub.add_parser("red-team", help="Run built-in anti-pseudoscience red-team checks.")
    rt.set_defaults(func=cmd_red_team)

    gate = sub.add_parser("gate", help="Run report quality gate on a generated report.")
    gate.add_argument("--input", required=True)
    gate.set_defaults(func=cmd_gate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    func: Callable[[argparse.Namespace], int] = args.func
    try:
        return int(func(args))
    except CliError as exc:
        if args.debug:
            raise
        print(f"BIVE_ERROR {exc.code}: {exc.detail}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
