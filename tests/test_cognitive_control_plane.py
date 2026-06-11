from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from bive.api import app, settings
from bive.cognitive_control import (
    ControlMode,
    cognitive_control_status,
    compute_weights,
    load_cognitive_control_contract,
    orchestrate_request,
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


def test_cognitive_control_contract_is_packaged() -> None:
    contract = load_cognitive_control_contract()
    assert contract["name"] == "BIVE Cognitive Control Plane"
    assert len(contract["agents"]) == 6
    assert set(contract["fractal_levels"]) == {"intent", "boundary", "contract", "verification", "release"}


def test_cognitive_weights_keep_bounds_and_balance() -> None:
    weights = compute_weights("Inspect repository gates and generate reversible remediation tasks")
    payload = weights.to_dict()
    assert all(0.0 <= value <= 1.0 for value in payload.values() if value != payload["balance_delta"])
    assert -1.0 <= payload["balance_delta"] <= 1.0
    assert weights.excitation > 0.0
    assert weights.inhibition >= 0.0


def test_high_risk_request_routes_to_human_gate() -> None:
    result = orchestrate_request("Deploy to production and rotate customer tokens")
    assert result.mode is ControlMode.HUMAN_GATE
    assert result.status.value == "HUMAN_REVIEW_REQUIRED"
    assert any(vote.veto for vote in result.agent_votes)
    assert "approval" in result.next_action.lower()


def test_low_risk_request_has_fractal_checks_and_reverse_plan() -> None:
    result = orchestrate_request("Inspect repository and propose reversible verification tasks")
    assert len(result.agent_votes) == 6
    assert len(result.fractal_checks) == 5
    assert all(check.passed for check in result.fractal_checks)
    assert result.reverse_inference_plan
    assert result.mode in {ControlMode.EXECUTE_BOUNDED, ControlMode.SPECIFY_ONLY}


def test_cognitive_control_status_exposes_release_gate() -> None:
    status = cognitive_control_status()
    assert status["release_gate"] == "make cognitive-control"
    assert status["sample_control_result"]["weights"]["stability_index"] >= 0.0


def test_cognitive_control_api_endpoint() -> None:
    response = TestClient(app).get(
        f"/api/v1/system/cognitive-control-plane?api-version={settings.api_version}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["release_gate"] == "make cognitive-control"
    assert data["sample_control_result"]["mode"] in {"EXECUTE_BOUNDED", "SPECIFY_ONLY"}


def test_cognitive_control_validator_script_passes(capsys) -> None:  # type: ignore[no-untyped-def]
    assert _load_script("scripts/validate_cognitive_control_plane.py").main() == 0
    assert "COGNITIVE_CONTROL_PASS" in capsys.readouterr().out
