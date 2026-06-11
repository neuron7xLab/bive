from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_WHEEL_MEMBERS = {
    "bive/api.py",
    "bive/web/index.html",
    "bive/web/static/app.js",
    "bive/web/static/styles.css",
    "bive/resources/product_operating_model.json",
    "bive/resources/industrial_release_scorecard.json",
    "bive-0.4.0.dist-info/entry_points.txt",
}


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    if env:
        clean_env.update(env)
    subprocess.run(cmd, cwd=cwd or ROOT, env=clean_env, check=True)


def _venv_python(path: Path) -> Path:
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> int:
    shutil.rmtree(ROOT / "dist", ignore_errors=True)
    run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(ROOT / "dist")])
    wheels = sorted((ROOT / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one wheel, found {wheels}")
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    missing = sorted(REQUIRED_WHEEL_MEMBERS - names)
    if missing:
        raise RuntimeError(f"wheel missing required members: {missing}")
    with tempfile.TemporaryDirectory(prefix="bive-wheel-smoke-") as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(venv_dir)
        python = _venv_python(venv_dir)
        run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)], cwd=Path(tmp))
        run(
            [
                str(python),
                "-c",
                "import bive.api; from importlib.resources import files; assert files('bive').joinpath('web/static/app.js').is_file(); assert files('bive.resources').joinpath('product_operating_model.json').is_file(); print('WHEEL_IMPORT_OK')",
            ],
            cwd=Path(tmp),
        )
    print("WHEEL_SMOKE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
