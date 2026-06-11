from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bive.science import validate_science_registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BIVE bounded science registry.")
    parser.add_argument(
        "--path",
        default=str(ROOT / "src" / "bive" / "resources" / "science_registry.json"),
        help="Path to science registry JSON.",
    )
    parser.add_argument(
        "--min-references",
        type=int,
        default=8,
        help="Minimum qualified references required for release.",
    )
    args = parser.parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_science_registry(data)
    if len(data["references"]) < args.min_references:
        raise SystemExit(f"SCIENCE_REGISTRY_FAIL references<{args.min_references}")
    Path("artifacts/verification").mkdir(parents=True, exist_ok=True)
    summary = {
        "registry_id": data["registry_id"],
        "disciplines": len(data["disciplines"]),
        "references": len(data["references"]),
        "status": data["status"],
    }
    Path("artifacts/verification/SCIENCE_REGISTRY_VALIDATION.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SCIENCE_REGISTRY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
