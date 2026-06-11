from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError as exc:
    raise SystemExit(
        "SCHEMA_VALIDATION_DEPENDENCY_MISSING: install the dev extra with `make bootstrap-env` "
        "or `pip install -e '.[dev]'`."
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    registry = Registry()
    for name, schema in schemas.items():
        registry = registry.with_resource(name, Resource.from_contents(schema))
    return registry


def validate_schema_documents(strict: bool) -> tuple[dict[str, dict[str, Any]], Registry]:
    schemas = {path.name: load_json(path) for path in sorted(SCHEMA_DIR.glob("*.json"))}
    registry = build_registry(schemas)
    for name, schema in schemas.items():
        if strict:
            Draft202012Validator.check_schema(schema)
        print(f"SCHEMA_OK {SCHEMA_DIR / name}")
    return schemas, registry


def validate_instances(schemas: dict[str, dict[str, Any]], registry: Registry) -> None:
    transcript_validator = Draft202012Validator(
        schemas["transcript_analyze_request.schema.json"], registry=registry
    )
    report_validator = Draft202012Validator(
        schemas["verification_report.schema.json"], registry=registry
    )

    sample = load_json(ROOT / "samples" / "demo_transcript.json")
    transcript = {"subject_scope": "sample", "segments": sample["segments"]}
    transcript_validator.validate(transcript)
    print(
        "INSTANCE_OK samples/demo_transcript.json:segments -> transcript_analyze_request.schema.json"
    )

    for path in sorted((ROOT / "artifacts").glob("demo_report*.json")):
        report_validator.validate(load_json(path))
        print(f"INSTANCE_OK {path.relative_to(ROOT)} -> verification_report.schema.json")

    invalid = {"segments": [{"text": "valid", "unexpected": True}], "unexpected": True}
    errors = list(transcript_validator.iter_errors(invalid))
    if not errors:
        raise RuntimeError("INVALID_FIXTURE_ACCEPTED transcript extra properties")
    print("NEGATIVE_INSTANCE_OK transcript extra properties rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--instances", action="store_true")
    args = parser.parse_args()
    schemas, registry = validate_schema_documents(strict=args.strict)
    if args.instances:
        validate_instances(schemas, registry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
