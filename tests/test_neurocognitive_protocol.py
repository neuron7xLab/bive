from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from bive.api import app, settings
from bive.neurocognitive import (
    load_neurocognitive_feature_map,
    load_neurocognitive_task_protocol,
    neurocognitive_protocol_status,
)


def _load_script(relative: str):  # type: ignore[no-untyped-def]
    path = Path(relative)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def test_neurocognitive_feature_map_has_operational_boundaries() -> None:
    feature_map = load_neurocognitive_feature_map()
    assert feature_map["status"] == "SPECIFIED_AND_TESTED"
    assert len(feature_map["features"]) == 8
    assert any("not" in claim.lower() or "no " in claim.lower() for claim in feature_map["forbidden_claims"])
    for feature in feature_map["features"]:
        assert feature["operational_function"]
        assert feature["validator"].startswith("scripts/")
        assert feature["failure_mode"]


def test_neurocognitive_task_protocol_tasks_are_executable() -> None:
    protocol = load_neurocognitive_task_protocol()
    ids = [task["id"] for task in protocol["tasks"]]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 8
    for task in protocol["tasks"]:
        assert task["exact_action"]
        assert task["artifact"]
        assert task["validator"]
        assert task["acceptance"]
        assert task["failure_signal"]


def test_salience_gating_blocks_decorative_terms() -> None:
    payload = load_neurocognitive_task_protocol()
    serialized = " ".join(task["exact_action"].lower() for task in payload["tasks"])
    assert "magic" not in serialized
    assert "conscious" not in serialized
    assert "brain-like" not in serialized


def test_neurocognitive_status_and_api_endpoint() -> None:
    status = neurocognitive_protocol_status()
    assert status["release_gate"] == "make neurocognitive-protocol"
    assert "diagnosis" in status["boundary"]
    response = TestClient(app).get(
        f"/api/v1/system/neurocognitive-protocol?api-version={settings.api_version}"
    )
    assert response.status_code == 200
    assert response.json()["release_gate"] == "make neurocognitive-protocol"


def test_neurocognitive_protocol_validator_script_passes(capsys) -> None:  # type: ignore[no-untyped-def]
    assert _load_script("scripts/validate_neurocognitive_protocol.py").main() == 0
    assert "NEUROCOGNITIVE_PROTOCOL_PASS" in capsys.readouterr().out
