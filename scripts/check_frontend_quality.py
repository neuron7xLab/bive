from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "src/bive/web/index.html"
JS = ROOT / "src/bive/web/static/app.js"
CSS = ROOT / "src/bive/web/static/styles.css"

REQUIRED_HTML_TOKENS = [
    "<main",
    'aria-live="polite"',
    'aria-labelledby="hero-title"',
    "<label",
    'id="apiToken"',
    'id="payload"',
    'id="statusText"',
    "skip-link",
    'id="scienceList"',
    'id="scienceBoundary"',
    'id="productReadiness"',
]
REQUIRED_JS_TOKENS = [
    "fetchJson",
    "/api/v1/system/status",
    "/api/v1/reports/from-transcript",
    "x-bive-api-key",
    "renderReport",
    "/api/v1/system/science-registry",
    "/api/v1/system/product-readiness",
    "renderScienceRegistry",
    "renderProductReadiness",
    "navigator.clipboard.writeText",
    "createElement",
    "textContent",
]
REQUIRED_CSS_TOKENS = [
    ":focus",
    "@media",
    "--gold",
    "status-dot",
    "prefers-reduced-motion",
    "grid-template-columns",
]
FORBIDDEN_JS_TOKENS = [
    "innerHTML",
    "outerHTML",
    "insertAdjacentHTML",
]


def check(path: Path, tokens: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [
        f"{path.relative_to(ROOT)} missing token: {token}" for token in tokens if token not in text
    ]


def main() -> int:
    errors: list[str] = []
    for path in (HTML, JS, CSS):
        if not path.exists():
            errors.append(f"missing asset: {path.relative_to(ROOT)}")
    if not errors:
        errors.extend(check(HTML, REQUIRED_HTML_TOKENS))
        errors.extend(check(JS, REQUIRED_JS_TOKENS))
        errors.extend(check(CSS, REQUIRED_CSS_TOKENS))
        js_text = JS.read_text(encoding="utf-8")
        for token in FORBIDDEN_JS_TOKENS:
            if token in js_text:
                errors.append(
                    f"{JS.relative_to(ROOT)} contains forbidden dynamic HTML token: {token}"
                )
    if errors:
        for error in errors:
            print(f"FRONTEND_QUALITY_ERROR {error}", file=sys.stderr)
        return 1
    print("FRONTEND_QUALITY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
