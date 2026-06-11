from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any, cast

REQUIRED_REFERENCE_FIELDS = {
    "id",
    "title",
    "authors",
    "year",
    "domain",
    "source_url",
    "operational_mapping",
    "claim_boundary",
}
REQUIRED_DISCIPLINE_FIELDS = {
    "id",
    "name",
    "operational_use",
    "allowed_claims",
    "blocked_claims",
    "references",
}
FORBIDDEN_BOUNDARY_PHRASES = (
    "automatic lie detection",
    "automatic liar label",
    "guilt inference",
    "intent inference",
    "diagnosis",
)


@lru_cache(maxsize=1)
def load_science_registry() -> dict[str, Any]:
    payload = (
        resources.files("bive.resources")
        .joinpath("science_registry.json")
        .read_text(encoding="utf-8")
    )
    data = json.loads(payload)
    validate_science_registry(data)
    return cast(dict[str, Any], data)


def validate_science_registry(data: dict[str, Any]) -> None:
    if data.get("status") != "bounded_reference_registry":
        raise ValueError("science registry status must be bounded_reference_registry")
    references = data.get("references")
    disciplines = data.get("disciplines")
    boundaries = data.get("hard_boundaries")
    if not isinstance(references, list) or not references:
        raise ValueError("science registry requires non-empty references")
    if not isinstance(disciplines, list) or not disciplines:
        raise ValueError("science registry requires non-empty disciplines")
    if not isinstance(boundaries, list) or not boundaries:
        raise ValueError("science registry requires hard_boundaries")

    reference_ids: set[str] = set()
    for ref in references:
        if not isinstance(ref, dict):
            raise ValueError("each reference must be an object")
        missing = REQUIRED_REFERENCE_FIELDS - set(ref)
        if missing:
            raise ValueError(
                f"reference {ref.get('id', '<missing>')} missing fields: {sorted(missing)}"
            )
        if not isinstance(ref["authors"], list) or not ref["authors"]:
            raise ValueError(f"reference {ref['id']} requires authors")
        if not str(ref["source_url"]).startswith("https://"):
            raise ValueError(f"reference {ref['id']} source_url must be https")
        if "not" not in str(ref["claim_boundary"]).lower():
            raise ValueError(f"reference {ref['id']} claim_boundary must state a negative boundary")
        reference_ids.add(str(ref["id"]))

    for discipline in disciplines:
        if not isinstance(discipline, dict):
            raise ValueError("each discipline must be an object")
        missing = REQUIRED_DISCIPLINE_FIELDS - set(discipline)
        if missing:
            raise ValueError(
                f"discipline {discipline.get('id', '<missing>')} missing fields: {sorted(missing)}"
            )
        refs = discipline.get("references")
        if not isinstance(refs, list) or not refs:
            raise ValueError(f"discipline {discipline['id']} requires references")
        unknown = sorted(set(map(str, refs)) - reference_ids)
        if unknown:
            raise ValueError(f"discipline {discipline['id']} references unknown ids: {unknown}")

    joined_boundaries = "\n".join(map(str, boundaries)).lower()
    for phrase in FORBIDDEN_BOUNDARY_PHRASES:
        if phrase.lower() not in joined_boundaries:
            raise ValueError(f"hard boundary must explicitly mention: {phrase}")


def science_registry_summary() -> dict[str, Any]:
    data = load_science_registry()
    return {
        "registry_id": data["registry_id"],
        "status": data["status"],
        "disciplines": [
            {"id": item["id"], "name": item["name"], "operational_use": item["operational_use"]}
            for item in data["disciplines"]
        ],
        "reference_count": len(data["references"]),
        "hard_boundaries": data["hard_boundaries"],
    }
