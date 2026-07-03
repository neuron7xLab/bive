from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app
from bive.benchmark import CONSTRUCT_CASES, run_construct_benchmark

API = "2026-06-11"


def test_benchmark_is_balanced_and_deterministic() -> None:
    labels = [label for label, _ in CONSTRUCT_CASES]
    assert sum(labels) == len(labels) - sum(labels)  # balanced 50/50
    first = run_construct_benchmark()
    second = run_construct_benchmark()
    assert first.to_dict() == second.to_dict()


def test_score_discriminates_above_chance() -> None:
    # The inconsistency score must rank contradiction-present above -absent
    # clearly above chance for the instrument to be worth publishing.
    result = run_construct_benchmark()
    assert result.roc_auc >= 0.7
    assert result.average_precision >= 0.7


def test_calibration_reduces_out_of_sample_error() -> None:
    result = run_construct_benchmark()
    # Cross-validated isotonic calibration should not worsen ECE.
    assert result.calibrated_ece_cv <= result.raw_ece + 1e-9


def test_calibration_endpoint_publishes_characteristics() -> None:
    client = TestClient(app)
    response = client.get(f"/api/v1/system/calibration?api-version={API}")
    assert response.status_code == 200
    body = response.json()
    assert "benchmark" in body
    b = body["benchmark"]
    for key in ("roc_auc", "average_precision", "raw_ece", "calibrated_ece_cv", "note"):
        assert key in b
    assert "construct" in b["note"].lower() or "construct" in b["construct"]


@pytest.mark.contract
def test_calibration_endpoint_requires_api_version() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/system/calibration").status_code == 400
