from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from bive.aos_cli import build_parser, cmd_product
from bive.api import app, settings
from bive.product import (
    load_industrial_release_scorecard,
    load_product_operating_model,
    product_readiness_status,
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


def test_product_model_preserves_hard_non_claims() -> None:
    model = load_product_operating_model()
    non_claims = " ".join(model["positioning"]["explicit_non_claims"]).lower()
    assert "lie detector" in non_claims
    assert "diagnosis" in non_claims
    assert "guilt" in non_claims
    assert model["release_policy"]["current_release_stage"] == "public_github_candidate"
    assert "deployed production" in model["release_policy"]["forbidden_claim"]


def test_industrial_scorecard_blocks_false_green() -> None:
    scorecard = load_industrial_release_scorecard()
    assert scorecard["overall_status"] == "YELLOW"
    statuses = {item["name"]: item["status"] for item in scorecard["dimensions"]}
    assert statuses["dependency_cve_audit"] == "UNKNOWN"
    assert statuses["docker_runtime"] == "UNKNOWN"
    assert statuses["human_impact_review"] == "HUMAN_REVIEW_REQUIRED"
    assert scorecard["decision"]["production_deploy"] == "BLOCK_UNTIL_EXTERNAL_GATES_CLOSE"


def test_product_readiness_runtime_status_is_inspectable() -> None:
    status = product_readiness_status()
    assert status["overall_status"] == "YELLOW"
    assert status["release_gate"] == "make product-readiness"
    assert "dependency_cve_audit" in status["blocking_unknowns"]
    assert "not deployed production" in status["boundary"]


def test_product_readiness_api_endpoint() -> None:
    response = TestClient(app).get(
        f"/api/v1/system/product-readiness?api-version={settings.api_version}"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "YELLOW"
    assert payload["release_scorecard"]["overall_status"] == "YELLOW"
    assert payload["product_model"]["model_id"] == "bive-industrial-product-operating-model-v1"


def test_product_cli_subcommand_outputs_status(capsys) -> None:  # type: ignore[no-untyped-def]
    parser = build_parser()
    args = parser.parse_args(["product"])
    assert cmd_product(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_status"] == "YELLOW"
    assert payload["release_gate"] == "make product-readiness"


def test_product_operating_model_validator_script_passes(capsys) -> None:  # type: ignore[no-untyped-def]
    assert _load_script("scripts/validate_product_operating_model.py").main() == 0
    assert "PRODUCT_READINESS_PASS" in capsys.readouterr().out
