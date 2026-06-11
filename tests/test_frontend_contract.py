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
    assert "sessionStorage" in js
    assert "localStorage" not in js
    assert "BiveAuthTokenManager" in js
    assert "renderReport" in js
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    assert "createElement" in js
    assert "@media" in css
    assert ":focus" in css
