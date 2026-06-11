from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_static_contract() -> None:
    html = (ROOT / "src/bive/web/index.html").read_text(encoding="utf-8")
    js = (ROOT / "src/bive/web/static/app.js").read_text(encoding="utf-8")
    css = (ROOT / "src/bive/web/static/styles.css").read_text(encoding="utf-8")
    assert 'aria-live="polite"' in html
    assert "<label" in html
    assert 'id="apiToken"' in html
    assert "apiUrl('/api/v1/system/status')" in js
    assert "api-version" in js
    assert "apiUrl('/api/v1/system/science-registry')" in js
    assert "apiUrl('/api/v1/system/product-readiness')" in js
    assert 'id="scienceList"' in html
    assert 'id="productReadiness"' in html
    assert "x-bive-api-key" in js
    assert "renderReport" in js
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    assert "createElement" in js
    assert "@media" in css
    assert ":focus" in css


def test_frontend_token_is_session_bounded() -> None:
    """The API token must never be persisted to localStorage and must be
    cleared on an unauthorized response (session-bounded lifecycle)."""
    js = (ROOT / "src/bive/web/static/app.js").read_text(encoding="utf-8")
    assert "localStorage" not in js, "API token must not be persisted to localStorage"
    assert "sessionStorage" in js, "API token must use session-bounded storage"
    assert "clearSessionToken" in js, "401 responses must clear the session token"
    assert "response.status === 401" in js, "unauthorized responses must drop the token"
    assert "history.replaceState" in js, "URL-supplied token must be scrubbed from the address bar"
