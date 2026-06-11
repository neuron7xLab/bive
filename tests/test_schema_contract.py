from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _registry() -> Registry:
    registry = Registry()
    for path in sorted((ROOT / "schemas").glob("*.json")):
        registry = registry.with_resource(path.name, Resource.from_contents(json.loads(path.read_text())))
    return registry


def test_transcript_schema_rejects_extra_fields() -> None:
    schema = _load("schemas/transcript_analyze_request.schema.json")
    validator = Draft202012Validator(schema)
    invalid = {"segments": [{"text": "valid", "unexpected": True}], "unexpected": True}
    assert list(validator.iter_errors(invalid))


def test_verification_report_schema_accepts_generated_demo() -> None:
    schema = _load("schemas/verification_report.schema.json")
    validator = Draft202012Validator(schema, registry=_registry())
    validator.validate(_load("artifacts/demo_report.json"))


def test_verification_report_schema_rejects_top_level_drift() -> None:
    schema = _load("schemas/verification_report.schema.json")
    validator = Draft202012Validator(schema, registry=_registry())
    invalid = deepcopy(_load("artifacts/demo_report.json"))
    invalid["unexpected"] = True
    assert list(validator.iter_errors(invalid))


def test_verification_report_schema_rejects_invalid_claim_shape() -> None:
    schema = _load("schemas/verification_report.schema.json")
    validator = Draft202012Validator(schema, registry=_registry())
    invalid = deepcopy(_load("artifacts/demo_report.json"))
    invalid["claims"][0].pop("text")  # type: ignore[index, union-attr]
    assert list(validator.iter_errors(invalid))
