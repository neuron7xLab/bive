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


def load_neurocognitive_feature_map() -> dict[str, Any]:
    return _load_resource("neurocognitive_feature_map.json")


def load_neurocognitive_task_protocol() -> dict[str, Any]:
    return _load_resource("neurocognitive_task_protocol.json")


def neurocognitive_protocol_status() -> dict[str, Any]:
    feature_map = load_neurocognitive_feature_map()
    task_protocol = load_neurocognitive_task_protocol()
    return {
        "feature_map": feature_map,
        "task_protocol": task_protocol,
        "release_gate": "make neurocognitive-protocol",
        "status": "SPECIFIED_AND_TESTED",
        "boundary": "CNS-inspired engineering analogies only; no biological identity, diagnosis, deception verdict or person-level mental-state claim.",
    }
