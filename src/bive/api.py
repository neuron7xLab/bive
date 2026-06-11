from __future__ import annotations

import argparse
import importlib.util
import sys
from typing import Any

MISSING_API_MESSAGE = (
    "BIVE_API_ERROR missing optional API dependencies. "
    "Install with `pip install -e '.[api]'` or `pip install -e '.[dev,api,security]'`."
)


class MissingAPIApp:
    """ASGI placeholder that fails closed when optional API dependencies are absent."""

    def __init__(self, missing: tuple[str, ...]) -> None:
        self.missing = missing

    async def __call__(self, _scope: dict[str, Any], _receive: Any, _send: Any) -> None:
        raise RuntimeError(f"{MISSING_API_MESSAGE} Missing: {', '.join(self.missing)}")


def missing_api_dependencies() -> tuple[str, ...]:
    return tuple(
        name for name in ("fastapi", "uvicorn") if importlib.util.find_spec(name) is None
    )


def _load_app() -> Any:
    missing = missing_api_dependencies()
    if missing:
        return MissingAPIApp(missing)
    from .api_runtime import app as runtime_app

    return runtime_app


def _load_settings() -> Any:
    """Expose runtime settings on the public ``bive.api`` surface.

    Returns ``None`` when the optional API extra is absent so that importing
    ``bive.api`` (and the core CLI) never requires FastAPI. Consumers that need
    settings must install the ``api`` extra; tests and the server runtime do.
    """
    if missing_api_dependencies():
        return None
    from .api_runtime import settings as runtime_settings

    return runtime_settings


app = _load_app()
settings = _load_settings()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bive-api",
        description="Run the BIVE FastAPI service. Requires the `api` extra.",
    )
    parser.add_argument("--host", default=None, help="Bind host; defaults to local/prod policy.")
    parser.add_argument("--port", type=int, default=8080, help="Bind port.")
    args = parser.parse_args(argv)

    missing = missing_api_dependencies()
    if missing:
        print(f"{MISSING_API_MESSAGE} Missing: {', '.join(missing)}", file=sys.stderr)
        return 1

    import uvicorn

    from .api_runtime import settings

    host = args.host or ("127.0.0.1" if settings.environment == "local" else "0.0.0.0")
    uvicorn.run("bive.api:app", host=host, port=args.port, reload=False)  # nosec B104
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
