from pathlib import Path

REQUIRED = [
    Path("src/bive/web/index.html"),
    Path("src/bive/web/static/styles.css"),
    Path("src/bive/web/static/app.js"),
]


def main() -> int:
    missing = [str(p) for p in REQUIRED if not p.exists()]
    if missing:
        print("UI_ASSET_FAIL")
        for item in missing:
            print("-", item)
        return 1
    html = Path("src/bive/web/index.html").read_text(encoding="utf-8")
    if "BIVE" not in html or "/static/app.js" not in html:
        print("UI_ASSET_FAIL invalid html contract")
        return 1
    print("UI_ASSET_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
