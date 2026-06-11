from __future__ import annotations

import importlib


def test_production_mode_requires_token(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("BIVE_ENV", "production")
    monkeypatch.delenv("BIVE_API_TOKEN", raising=False)
    import bive.settings as settings_module

    importlib.reload(settings_module)
    settings = settings_module.get_settings()
    assert settings.auth_required is True
    assert (
        "BIVE_API_TOKEN is required when BIVE_ENV is production/staging" in settings.config_errors
    )
