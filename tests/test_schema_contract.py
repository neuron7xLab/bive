from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def test_transcript_schema_rejects_extra_fields() -> None:
    schema = json.loads((ROOT / "schemas/transcript_analyze_request.schema.json").read_text())
    validator = Draft202012Validator(schema)
    invalid = {"segments": [{"text": "valid", "unexpected": True}], "unexpected": True}
    assert list(validator.iter_errors(invalid))
