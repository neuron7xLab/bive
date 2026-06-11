from __future__ import annotations

import os
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path

_ALLOWED_ENVIRONMENTS = {"local", "development", "dev", "test", "staging", "production", "prod"}


def _package_version() -> str:
    try:
        return metadata.version("bive")
    except metadata.PackageNotFoundError:
        return "0.4.0"


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _raw(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value is not None else None


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("BIVE_APP_NAME", "BIVE"))
    version: str = field(default_factory=_package_version)
    environment: str = field(default_factory=lambda: os.getenv("BIVE_ENV", "local"))
    storage_path: Path = field(
        default_factory=lambda: Path(os.getenv("BIVE_STORAGE", ".bive/bive.sqlite3"))
    )
    artifact_dir: Path = field(
        default_factory=lambda: Path(os.getenv("BIVE_ARTIFACT_DIR", "artifacts"))
    )
    max_upload_bytes: int = field(
        default_factory=lambda: _int_env("BIVE_MAX_UPLOAD_BYTES", 25_000_000)
    )
    max_segments: int = field(default_factory=lambda: _int_env("BIVE_MAX_SEGMENTS", 2_000))
    max_text_chars: int = field(default_factory=lambda: _int_env("BIVE_MAX_TEXT_CHARS", 10_000))
    api_token: str | None = field(default_factory=lambda: os.getenv("BIVE_API_TOKEN") or None)
    allow_person_level_verdicts: bool = field(
        default_factory=lambda: _bool_env("BIVE_ALLOW_PERSON_LEVEL_VERDICTS", False)
    )
    api_version: str = field(default_factory=lambda: os.getenv("BIVE_API_VERSION", "2026-06-11"))

    @property
    def production_mode(self) -> bool:
        return self.environment.lower() in {"production", "prod", "staging"}

    @property
    def auth_required(self) -> bool:
        return self.production_mode

    @property
    def config_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.environment.lower() not in _ALLOWED_ENVIRONMENTS:
            errors.append(
                "BIVE_ENV must be one of local/development/dev/test/staging/production/prod"
            )
        for name in ("BIVE_MAX_UPLOAD_BYTES", "BIVE_MAX_SEGMENTS", "BIVE_MAX_TEXT_CHARS"):
            raw = _raw(name)
            if raw is not None:
                try:
                    int(raw)
                except ValueError:
                    errors.append(f"{name} must be an integer")
        if self.max_upload_bytes <= 0:
            errors.append("BIVE_MAX_UPLOAD_BYTES must be positive")
        if self.max_segments <= 0:
            errors.append("BIVE_MAX_SEGMENTS must be positive")
        if self.max_text_chars <= 0:
            errors.append("BIVE_MAX_TEXT_CHARS must be positive")
        if not self.api_version:
            errors.append("BIVE_API_VERSION must be non-empty")
        if self.auth_required and not self.api_token:
            errors.append("BIVE_API_TOKEN is required when BIVE_ENV is production/staging")
        if self.auth_required and self.allow_person_level_verdicts:
            errors.append(
                "BIVE_ALLOW_PERSON_LEVEL_VERDICTS cannot be enabled in production/staging"
            )
        return tuple(errors)


def get_settings() -> Settings:
    return Settings()
