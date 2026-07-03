"""Phase 0 subject-independent cross-validation with honest calibration.

GroupKFold by speaker/session/source so the same subject never appears in train
and test — the discrimination number is subject-independent, not fold-leaky.
Reports AUC (+ bootstrap CI), ECE and Brier before *and* after isotonic
calibration, and a 10-bin reliability diagram. Requires the optional ``ml`` /
``cogveritas`` extra (numpy + scikit-learn); raises a clear error otherwise.
"""

from __future__ import annotations

from importlib import util as _import_util

from .calibration_metrics import (
    bootstrap_ci,
    brier_score,
    expected_calibration_error,
    reliability_diagram,
    roc_auc,
)

_SKLEARN = _import_util.find_spec("sklearn") is not None


def sklearn_available() -> bool:
    return _SKLEARN


def run_group_cv(
    features: list[list[float]],
    labels: list[int],
    groups: list[object],
    *,
    n_splits: int = 5,
    seed: int = 20260703,
    n_bootstrap: int = 1000,
) -> dict[str, object]:
    """Subject-independent CV. Returns the full Phase 0 metric block."""
    if not _SKLEARN:
        raise RuntimeError(
            "scikit-learn is required for Phase 0 CV: pip install -e '.[cogveritas]'"
        )
    from importlib import import_module  # noqa: PLC0415

    np = import_module("numpy")  # via importlib so mypy does not load numpy's stubs
    from sklearn.calibration import CalibratedClassifierCV  # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
    from sklearn.model_selection import GroupKFold  # noqa: PLC0415
    from sklearn.pipeline import make_pipeline  # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler  # noqa: PLC0415

    x = np.asarray(features, dtype=float)
    y = np.asarray(labels, dtype=int)
    g = np.asarray([str(v) for v in groups])
    n_groups = len(set(g.tolist()))
    splits = min(n_splits, n_groups)

    p_before = np.zeros(len(y))
    p_after = np.zeros(len(y))
    gkf = GroupKFold(n_splits=splits)
    for tr, te in gkf.split(x, y, g):
        base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        base.fit(x[tr], y[tr])
        p_before[te] = base.predict_proba(x[te])[:, 1]
        inner = min(3, len(np.unique(y[tr])) + 1, len(tr))
        cal = CalibratedClassifierCV(
            make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
            method="isotonic",
            cv=max(2, inner),
        )
        cal.fit(x[tr], y[tr])
        p_after[te] = cal.predict_proba(x[te])[:, 1]

    yl = y.tolist()
    return {
        "n_samples": int(len(y)),
        "n_groups": int(n_groups),
        "n_folds": int(splits),
        "positive_rate": round(float(y.mean()), 6),
        "auc": round(roc_auc(yl, p_after.tolist()), 6),
        "auc_ci": list(bootstrap_ci(yl, p_after.tolist(), n_boot=n_bootstrap, seed=seed)),
        "ece_before": round(expected_calibration_error(yl, p_before.tolist()), 6),
        "ece_after": round(expected_calibration_error(yl, p_after.tolist()), 6),
        "brier_before": round(brier_score(yl, p_before.tolist()), 6),
        "brier_after": round(brier_score(yl, p_after.tolist()), 6),
        "reliability_diagram": reliability_diagram(yl, p_after.tolist(), bins=10),
    }
