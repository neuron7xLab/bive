"""Analyst dossier — Markdown rendering + endpoint format negotiation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bive.api import app
from bive.cogveritas.output_contract import FORBIDDEN_JUDGMENT_STRINGS
from bive.cogveritas.service import analyze_dossier_markdown

API = "2026-06-11"
EP = "/api/v1/cogveritas/verifiability"

_UK_CASE = (
    "3 березня о 14:30 я передав Петру 5000 гривень готівкою. "
    "Я не передавав Петру жодних грошей. "
    "Я підписав договір оренди. "
    "Я думаю, він нервував."
)


def test_dossier_has_all_sections_in_ukrainian() -> None:
    md = analyze_dossier_markdown(_UK_CASE)
    assert "# Досьє перевірюваності" in md
    assert "Вирок: відсутній" in md
    assert "## Хронологія" in md
    assert "## Потенційні суперечності" in md
    assert "## Лист корроборації" in md
    assert "## Провенанс" in md
    assert "## Межі та наукова основа" in md
    assert "docs/EMPIRICAL_VALIDATION.md" in md


def test_dossier_never_contains_a_verdict_framing() -> None:
    import re

    md = analyze_dossier_markdown("He is lying about the money. She paid 500 dollars in Chicago Friday.")
    # Strip quoted evidence spans; the system's own framing must be clean.
    framing = re.sub(r"«[^»]*»", "«…»", md).lower()
    assert all(s not in framing for s in FORBIDDEN_JUDGMENT_STRINGS)


@pytest.mark.contract
def test_endpoint_returns_markdown_dossier() -> None:
    client = TestClient(app)
    r = client.post(f"{EP}?api-version={API}&format=markdown", content=_UK_CASE)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "# Досьє перевірюваності" in r.text


@pytest.mark.contract
def test_endpoint_rejects_unknown_format() -> None:
    client = TestClient(app)
    r = client.post(f"{EP}?api-version={API}&format=pdf", content="x y z")
    assert r.status_code == 422  # pattern-validated query param


@pytest.mark.contract
def test_json_still_default_and_carries_language() -> None:
    client = TestClient(app)
    r = client.post(f"{EP}?api-version={API}", content=_UK_CASE)
    assert r.status_code == 200
    assert r.json()["detected_language"] == "uk"
