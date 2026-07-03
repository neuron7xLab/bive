from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app
from bive.cogveritas.output_contract import FORBIDDEN_JUDGMENT_STRINGS

API = "2026-06-11"
EP = "/api/v1/cogveritas/verifiability"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.contract
def test_verifiability_endpoint_never_returns_a_verdict(client: TestClient) -> None:
    r = client.post(f"{EP}?api-version={API}", content="I met John Smith at the Hilton on March 3.")
    assert r.status_code == 200
    d = r.json()
    assert d["verdict"] is None
    assert d["calibrated_probability"] is None  # Phase 0: floats disabled
    assert d["ordinal_flag"] in {"markers_elevated", "markers_nominal", "insufficient_data"}
    assert d["corroboration_questions"]
    assert d["audit_trail"]


@pytest.mark.contract
def test_system_framing_has_no_forbidden_judgment_even_on_judgmental_input(client: TestClient) -> None:
    # Input contains judgment words ("is lying"); the system may quote them as
    # evidence but must never emit them as its OWN framing, and never a verdict.
    import re

    r = client.post(
        f"{EP}?api-version={API}",
        content="He is lying about the money. She paid 500 dollars in Chicago on Friday.",
    )
    assert r.status_code == 200
    d = r.json()
    assert d["verdict"] is None
    quote = re.compile(r"«[^»]*»")
    for field in [*d["corroboration_questions"], *d["rm_criteria_flagged"]]:
        framing = quote.sub("«…»", field).lower()
        assert all(s not in framing for s in FORBIDDEN_JUDGMENT_STRINGS)


@pytest.mark.contract
def test_verifiability_requires_api_version(client: TestClient) -> None:
    assert client.post(EP, content="x").status_code == 400


@pytest.mark.contract
def test_verifiability_fails_closed_on_empty(client: TestClient) -> None:
    assert client.post(f"{EP}?api-version={API}", content="").status_code == 422


@pytest.mark.contract
def test_verifiability_gap_is_ordinal_not_probability(client: TestClient) -> None:
    r = client.post(
        f"{EP}?api-version={API}",
        content="I think it was wonderful and amazing and perfect and lovely and great overall.",
    )
    d = r.json()
    assert d["verifiability_gap"] in {"elevated", "nominal", "insufficient"}
    assert d["calibrated_probability"] is None
