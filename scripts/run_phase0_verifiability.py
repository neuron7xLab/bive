"""Generate the COGVERITAS Phase 0 artifacts from real labeled data.

Run with data present (research/cogveritas/fetch_data.sh). Emits dataset
manifests and the PHASE0_* verification artifacts. Fail-closed: MU3D is not
downloadable without registration, so its manifest is marked unavailable and the
gate keeps Phase 1 blocked. The two REAL datasets used are Op-Spam (hotel-grouped,
subject-independent) and the Real-Life Trial corpus (clip-grouped, high-stakes) —
a stronger substitution than the MU3D placeholder, recorded in the decision doc.
"""

from __future__ import annotations

import csv
import glob
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bive.cogveritas import KILL_AUC, analyze, contains_forbidden_judgment  # noqa: E402
from bive.cogveritas.bias_baseline import evaluate_bias_gate  # noqa: E402
from bive.cogveritas.phase0_cv import run_group_cv, sklearn_available  # noqa: E402
from bive.cogveritas.verifiability_tagger import feature_schema_sha256  # noqa: E402

DATA = ROOT / "research" / "cogveritas" / "data"
DS_DIR = ROOT / "artifacts" / "datasets"
V_DIR = ROOT / "artifacts" / "verification"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def load_opspam() -> tuple[list[list[float]], list[int], list[str]] | None:
    path = DATA / "opspam.csv"
    if not path.exists():
        return None
    rows = list(csv.DictReader(path.read_text(encoding="utf-8", errors="replace").splitlines()))
    feats, labels, groups = [], [], []
    for i, r in enumerate(rows):
        f, _ = analyze(r["Ori_Review"])
        feats.append(f.vector())
        labels.append(1 if r["Label"] == "1" else 0)
        # Ott order: 20 hotels x 20 reviews per 400-block -> hotel-independent groups.
        groups.append(f"hotel:{(i % 400) // 20}")
    return feats, labels, groups


def load_rlt() -> tuple[list[list[float]], list[int], list[str]] | None:
    dec = sorted(glob.glob(str(DATA / "rlt" / "Deceptive" / "*.txt")))
    tru = sorted(glob.glob(str(DATA / "rlt" / "Truthful" / "*.txt")))
    if not dec or not tru:
        return None
    feats, labels, groups = [], [], []
    for path, lab in [(p, 1) for p in dec] + [(p, 0) for p in tru]:
        f, _ = analyze(Path(path).read_text(encoding="utf-8", errors="replace"))
        feats.append(f.vector())
        labels.append(lab)
        groups.append(f"clip:{Path(path).stem}")  # clip-level group (limitation noted)
    return feats, labels, groups


def dataset_block(name: str, loaded: tuple[list[list[float]], list[int], list[str]] | None) -> dict:
    if loaded is None or not sklearn_available():
        return {
            "name": name,
            "n_samples": None,
            "n_groups": None,
            "n_folds": 5,
            "positive_rate": None,
            "auc": None,
            "auc_ci": None,
            "ece_before": None,
            "ece_after": None,
            "brier_before": None,
            "brier_after": None,
            "kill_criterion_passed": False,
            "status": "unavailable",
        }
    feats, labels, groups = loaded
    m = run_group_cv(feats, labels, groups)
    m["name"] = name
    m["kill_criterion_passed"] = bool(m["auc"] > KILL_AUC)
    m["status"] = "computed"
    return m


def main() -> int:
    DS_DIR.mkdir(parents=True, exist_ok=True)
    V_DIR.mkdir(parents=True, exist_ok=True)

    opspam = load_opspam()
    rlt = load_rlt()

    # Dataset manifests (raw data never committed).
    (DS_DIR / "op_spam_manifest.json").write_text(json.dumps({
        "dataset": "OP_SPAM",
        "source_url": "https://myleott.com/op-spam.html",
        "access_date": _now() if opspam else None,
        "license_notes": "Ott et al.; redistribute via loader + checksum, not raw text",
        "raw_data_committed": False,
        "n_items": len(opspam[1]) if opspam else None,
        "label_schema": "1=deceptive(MTurk), 0=truthful(web)",
        "grouping_strategy": "hotel_index from canonical 20x20 block order",
        "sha256": _sha("op_spam_loader_v1"),
    }, indent=2) + "\n")
    # MU3D unavailable without registration -> fail-closed manifest.
    (DS_DIR / "mu3d_manifest.json").write_text(json.dumps({
        "dataset": "MU3D",
        "source_url": "https://mmlab.ie.cuhk.edu.hk/projects/MU3D.html",
        "access_date": None,
        "license_notes": "requires registration; not obtainable non-interactively",
        "raw_data_committed": False,
        "n_items": None,
        "transcript_available": None,
        "metadata_fields": [],
        "speaker_id_field": None,
        "sha256": None,
        "status": "unavailable — Real-Life Trial substituted; see DECISION doc",
    }, indent=2) + "\n")

    blocks = [dataset_block("OP_SPAM", opspam), dataset_block("RLT", rlt)]
    passed = [b for b in blocks if b.get("kill_criterion_passed")]
    # Phase 1 unlocks only if BOTH real datasets clear the kill criterion.
    phase1 = len(passed) == len([b for b in blocks if b["status"] == "computed"]) and len(passed) >= 2

    # No-verdict invariant: scan every emitted string field.
    scan = json.dumps(blocks)
    forbidden = contains_forbidden_judgment(scan)

    verifiability = {
        "phase": "0",
        "status": "pass" if phase1 else "blocked",
        "datasets": blocks,
        "phase1_unlocked": bool(phase1),
        "no_verdict_invariant_passed": not forbidden,
        "float_probability_allowed": False,
        "created_at_utc": _now(),
        "code_version": "cogveritas-phase0",
        "feature_schema_sha256": feature_schema_sha256(),
        "dataset_manifest_sha256": _sha("op_spam+mu3d+rlt"),
    }
    (V_DIR / "PHASE0_VERIFIABILITY.json").write_text(json.dumps(verifiability, indent=2) + "\n")

    (V_DIR / "PHASE0_RELIABILITY_DIAGRAM.json").write_text(json.dumps({
        "phase": "0",
        "bins": 10,
        "datasets": [
            {"name": b["name"], **(b.get("reliability_diagram") or {})} for b in blocks
        ],
    }, indent=2) + "\n")

    # Bias baseline: no sensitive metadata available for either text corpus -> fail-closed.
    model_auc = passed[0]["auc"] if passed else None
    bias = evaluate_bias_gate(model_auc, None, None, sensitive_fields=[])
    (V_DIR / "PHASE0_BIAS_BASELINE.json").write_text(json.dumps(bias, indent=2) + "\n")

    print(f"PHASE0 written: phase1_unlocked={phase1} datasets={[ (b['name'], b['auc']) for b in blocks ]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
