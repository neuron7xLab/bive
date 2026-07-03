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


def test_cogveritas_verifiability_ui_is_wired() -> None:
    """The verifiability mode must stay wired end-to-end in the static frontend:
    a trigger, a fetch to the live endpoint, and a renderer that surfaces the
    no-verdict framing. Browser-only JS has no runtime test, so this guards the
    wiring from silent regression."""
    html = (ROOT / "src/bive/web/index.html").read_text(encoding="utf-8")
    js = (ROOT / "src/bive/web/static/app.js").read_text(encoding="utf-8")
    assert 'id="verify"' in html, "verifiability trigger button must exist"
    assert "apiUrl('/api/v1/cogveritas/verifiability')" in js
    assert "renderVerifiability" in js, "verifiability renderer must exist"
    assert "corroboration_questions" in js
    assert "verifiability_gap" in js
    # The no-verdict invariant must be surfaced to the user, not just enforced
    # server-side; the renderer must never present a person-level verdict.
    assert "вирок: відсутній" in js, "renderer must surface the no-verdict framing"
    for forbidden in ("verdict: true", "verdict: false", "is lying", "is truthful"):
        assert forbidden not in js.lower(), f"frontend must not render a verdict: {forbidden!r}"
    # Verifiability must accept an attached transcript file, not only the textarea,
    # and reuse the same media/size guards as the main analysis path.
    assert "resolveVerifiabilityInput" in js, "verifiability must resolve file or textarea input"
    assert "pendingFile" in js and "MEDIA_EXTENSIONS" in js, "file path must reuse upload guards"
    # The no-verdict posture must be explainable in-product: a progressive-
    # disclosure that fetches the empirical methodology contract.
    assert "methodologyDisclosure" in js
    assert "apiUrl('/api/v1/cogveritas/methodology')" in js
    assert "empirical_law" in js
    # The corroboration worklist (record-type routing) must render.
    assert "corroboration_worklist" in js
    assert "record_types" in js
    # Timeline and review-worthy conflicts must render.
    assert "data.timeline" in js
    assert "data.conflicts" in js
    assert "negation_polarity" in js and "figure_mismatch" in js
    # The analyst dossier must be exportable.
    assert "downloadDossier" in js
    assert "format=markdown" in js


def test_frontend_token_is_session_bounded() -> None:
    """The API token must never be persisted to localStorage and must be
    cleared on an unauthorized response (session-bounded lifecycle)."""
    js = (ROOT / "src/bive/web/static/app.js").read_text(encoding="utf-8")
    assert "localStorage" not in js, "API token must not be persisted to localStorage"
    assert "sessionStorage" in js, "API token must use session-bounded storage"
    assert "clearSessionToken" in js, "401 responses must clear the session token"
    assert "response.status === 401" in js, "unauthorized responses must drop the token"
    assert "history.replaceState" in js, "URL-supplied token must be scrubbed from the address bar"
