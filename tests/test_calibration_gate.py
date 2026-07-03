from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from bive.benchmark import CALIBRATION_THRESHOLDS, calibration_gate
from bive.calibration_metrics import bootstrap_interval, roc_auc
from bive.ingest import TranscriptSegment
from bive.report import build_report_from_segments

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_interval_is_deterministic_and_bracketing() -> None:
    labels = [0, 0, 0, 1, 1, 1, 0, 1]
    scores = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 0.4, 0.6]
    a = bootstrap_interval(roc_auc, labels, scores, n_boot=200)
    b = bootstrap_interval(roc_auc, labels, scores, n_boot=200)
    assert a.to_dict() == b.to_dict()  # seeded -> reproducible
    assert a.lower <= a.point <= a.upper
    assert a.resamples > 0


def test_calibration_gate_passes_and_reports_intervals() -> None:
    gate = calibration_gate()
    assert gate["passed"] is True
    names = {c["name"] for c in gate["checks"]}  # type: ignore[union-attr]
    assert names == {
        "roc_auc_floor",
        "average_precision_floor",
        "othello_specificity",
        "calibration_not_worsened",
    }
    assert gate["thresholds"] == CALIBRATION_THRESHOLDS
    for key in ("roc_auc_ci", "ece_ci"):
        ci = gate[key]
        assert set(ci) == {"point", "lower", "upper", "resamples"}  # type: ignore[arg-type]


def test_cognitive_load_hypothesis_activates() -> None:
    # Repetitive, low-diversity long text is a weak cognitive-load cue and must
    # populate the previously-inert cognitive_load_risk hypothesis.
    text = "I want to say that I want to say the same thing again and again. " * 6
    report = build_report_from_segments([TranscriptSegment("s", text, 0, 1)])
    cog = next(h for h in report.hypotheses if h.label == "cognitive_load_risk")
    assert cog.evidence_for  # no longer inert
    assert any(e.feature == "cognitive_load_markers" for e in report.evidence_events)


def test_calibration_script_writes_tamper_evident_artifact(tmp_path: Path) -> None:
    env = {"PYTHONPATH": str(ROOT / "src"), "BIVE_STORAGE": str(tmp_path / "s.sqlite3"), "PATH": ""}
    import os

    env = {**os.environ, **env}
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_calibration.py")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert "CALIBRATION_GATE_PASS" in proc.stdout
    artifact = json.loads((ROOT / "artifacts" / "verification" / "CALIBRATION.json").read_text())
    integrity = artifact["integrity"]
    assert integrity["algorithm"] == "sha256"
    payload = {k: v for k, v in artifact.items() if k != "integrity"}
    recomputed = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert recomputed == integrity["content_digest"]
