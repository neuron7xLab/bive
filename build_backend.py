from __future__ import annotations

import base64
import csv
import hashlib
import os
import shutil
import zipfile
from collections.abc import Iterable
from pathlib import Path

NAME = "bive"
VERSION = "0.4.0"
DIST_INFO = f"{NAME}-{VERSION}.dist-info"
SUMMARY = "Behavioral Integrity Verification Engine: evidence-first transcript verification, falsification and review system."
ROOT = Path(__file__).resolve().parent

CORE_REQUIRES = ["pydantic>=2.6,<3"]
EXTRAS = {
    "dev": [
        "pytest>=8,<10",
        "pytest-cov>=5,<8",
        "ruff>=0.6,<1",
        "mypy>=1.10,<3",
        "jsonschema>=4,<5",
        "httpx>=0.27,<1",
        "bandit>=1.7,<2",
        "build>=1.2,<2",
        "pip-licenses>=5,<6",
        "pip-tools>=7,<8",
        "tomli>=2,<3; python_version < '3.11'",
    ],
    "security": ["bandit>=1.7,<2", "pip-audit>=2.7,<3", "cyclonedx-bom>=5,<8", "pip-licenses>=5,<6"],
    "ml": ["numpy>=1.26,<3", "pandas>=2,<3", "scikit-learn>=1.4,<2"],
    "media": ["openai-whisper", "pyannote.audio", "opensmile", "opencv-python"],
    "api": ["fastapi>=0.110,<1", "uvicorn[standard]>=0.27,<1"],
    "ops": ["dvc>=3,<4", "mlflow>=2,<4", "evidently>=0.4,<1"],
}
EXTRAS["all"] = ["bive[dev,api,ml,media,ops]"]
ENTRY_POINTS = """[console_scripts]\nbive = bive.cli:main\nbive-pr-check = bive.pr_gate:main\nbive-api = bive.api:main\nbive-aos = bive.aos_cli:main\nbive-cognitive-control = bive.cognitive_control:main\n"""


def _metadata_text() -> str:
    lines = [
        "Metadata-Version: 2.3",
        f"Name: {NAME}",
        f"Version: {VERSION}",
        f"Summary: {SUMMARY}",
        "License-Expression: Apache-2.0",
        "Requires-Python: >=3.10",
        "Project-URL: Homepage, https://github.com/neuron7xLab/bive",
        "Project-URL: Repository, https://github.com/neuron7xLab/bive",
        "Project-URL: Issues, https://github.com/neuron7xLab/bive/issues",
        "Project-URL: Documentation, https://github.com/neuron7xLab/bive/tree/main/docs",
    ]
    for req in CORE_REQUIRES:
        lines.append(f"Requires-Dist: {req}")
    for extra, reqs in EXTRAS.items():
        lines.append(f"Provides-Extra: {extra}")
        for req in reqs:
            if ";" in req:
                requirement, marker = req.split(";", 1)
                lines.append(f"Requires-Dist: {requirement.strip()}; ({marker.strip()}) and extra == '{extra}'")
            else:
                lines.append(f"Requires-Dist: {req}; extra == '{extra}'")
    lines.extend(["", SUMMARY, ""])
    return "\n".join(lines)


def _wheel_text() -> str:
    return "Wheel-Version: 1.0\nGenerator: bive-build-backend\nRoot-Is-Purelib: true\nTag: py3-none-any\n"


def _write_metadata_dir(base: Path) -> Path:
    dist = base / DIST_INFO
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "METADATA").write_text(_metadata_text(), encoding="utf-8")
    (dist / "WHEEL").write_text(_wheel_text(), encoding="utf-8")
    (dist / "entry_points.txt").write_text(ENTRY_POINTS, encoding="utf-8")
    return dist


def _hash(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _iter_package_files() -> Iterable[Path]:
    for path in sorted((ROOT / "src" / "bive").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            yield path


def _write_wheel(wheel_directory: str, *, editable: bool) -> str:
    wheel_name = f"{NAME}-{VERSION}-py3-none-any.whl"
    wheel_path = Path(wheel_directory) / wheel_name
    records: list[tuple[str, str, str]] = []

    def write_file(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
        zf.writestr(arcname, data)
        records.append((arcname, _hash(data), str(len(data))))

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if editable:
            write_file(zf, "bive_editable.pth", str((ROOT / "src").resolve()).encode("utf-8") + b"\n")
        else:
            for path in _iter_package_files():
                arcname = str(path.relative_to(ROOT / "src")).replace(os.sep, "/")
                write_file(zf, arcname, path.read_bytes())
        write_file(zf, f"{DIST_INFO}/METADATA", _metadata_text().encode("utf-8"))
        write_file(zf, f"{DIST_INFO}/WHEEL", _wheel_text().encode("utf-8"))
        write_file(zf, f"{DIST_INFO}/entry_points.txt", ENTRY_POINTS.encode("utf-8"))
        records.append((f"{DIST_INFO}/RECORD", "", ""))
        record_rows = []
        for row in records:
            record_rows.append(row)
        from io import StringIO

        buf = StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerows(record_rows)
        zf.writestr(f"{DIST_INFO}/RECORD", buf.getvalue().encode("utf-8"))
    return wheel_name


def get_requires_for_build_wheel(config_settings: object | None = None) -> list[str]:
    return []


def get_requires_for_build_editable(config_settings: object | None = None) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings: object | None = None) -> str:
    _write_metadata_dir(Path(metadata_directory))
    return DIST_INFO


def prepare_metadata_for_build_editable(metadata_directory: str, config_settings: object | None = None) -> str:
    _write_metadata_dir(Path(metadata_directory))
    return DIST_INFO


def build_wheel(wheel_directory: str, config_settings: object | None = None, metadata_directory: str | None = None) -> str:
    return _write_wheel(wheel_directory, editable=False)


def build_editable(wheel_directory: str, config_settings: object | None = None, metadata_directory: str | None = None) -> str:
    return _write_wheel(wheel_directory, editable=True)


def build_sdist(sdist_directory: str, config_settings: object | None = None) -> str:
    archive = shutil.make_archive(str(Path(sdist_directory) / f"{NAME}-{VERSION}"), "gztar", ROOT)
    return Path(archive).name
