from __future__ import annotations

from importlib import metadata
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 ships no stdlib tomllib
    import tomli as tomllib
from fastapi.testclient import TestClient

from bive.api import app
from bive.settings import get_settings


def expected_version() -> str:
    try:
        return metadata.version("bive")
    except metadata.PackageNotFoundError:
        project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
        return str(project["version"])


def test_settings_version_matches_package_metadata() -> None:
    assert get_settings().version == expected_version()


def test_api_health_version_matches_package_metadata() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == expected_version()
