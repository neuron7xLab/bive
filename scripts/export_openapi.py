from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("BIVE_STORAGE", str(Path(tempfile.gettempdir()) / "bive-openapi.sqlite3"))

from bive.api import app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/openapi.json")
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = Path(args.output)
    payload = json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check and output.exists() and output.read_text(encoding="utf-8") != payload:
        print(
            f"OPENAPI_ERROR {output} is stale; run make openapi without --check or make manifest",
            file=sys.stderr,
        )
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload, encoding="utf-8")
    print(f"OPENAPI_PASS {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
