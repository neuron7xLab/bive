from pathlib import Path


def test_ui_assets_exist() -> None:
    assert Path("src/bive/web/index.html").exists()
    assert Path("src/bive/web/static/styles.css").exists()
    assert Path("src/bive/web/static/app.js").exists()
