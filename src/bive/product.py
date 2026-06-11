from __future__ import annotations

import json
from importlib import resources
from typing import Any


def _load_resource(name: str) -> dict[str, Any]:
    with resources.files("bive.resources").joinpath(name).open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return data


def load_product_operating_model() -> dict[str, Any]:
    return _load_resource("product_operating_model.json")


def load_industrial_release_scorecard() -> dict[str, Any]:
    return _load_resource("industrial_release_scorecard.json")


def product_readiness_status() -> dict[str, Any]:
    model = load_product_operating_model()
    scorecard = load_industrial_release_scorecard()
    dimensions = scorecard.get("dimensions", [])
    if not isinstance(dimensions, list):
        dimensions = []
    counts: dict[str, int] = {}
    for item in dimensions:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    blocked = counts.get("UNKNOWN", 0) > 0 or counts.get("HUMAN_REVIEW_REQUIRED", 0) > 0
    return {
        "product_model": model,
        "release_scorecard": scorecard,
        "stage": model.get("release_policy", {}).get("current_release_stage", "unknown")
        if isinstance(model.get("release_policy"), dict)
        else "unknown",
        "overall_status": "YELLOW" if blocked else str(scorecard.get("overall_status", "UNKNOWN")),
        "dimension_counts": counts,
        "release_gate": "make product-readiness",
        "blocking_unknowns": [
            item.get("name")
            for item in dimensions
            if isinstance(item, dict) and item.get("status") in {"UNKNOWN", "HUMAN_REVIEW_REQUIRED"}
        ],
        "boundary": "GitHub product candidate; not deployed production, not diagnostic, not lie detection, not a person-impacting decision system.",
    }
