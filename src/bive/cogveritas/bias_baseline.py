"""Mambreyan-style bias baseline — fail-closed.

If a classifier using ONLY a sensitive attribute (e.g. gender) matches or beats
the real model, the model's "accuracy" is demographic leakage, not the intended
verifiability signal, and release is blocked. If the sensitive metadata is
unavailable, the gate does NOT silently pass — release stays blocked pending an
explicit human-review record.
"""

from __future__ import annotations

from importlib import util as _import_util

from .calibration_metrics import roc_auc

_SKLEARN = _import_util.find_spec("sklearn") is not None


def sensitive_only_auc(
    sensitive: list[list[float]], labels: list[int], *, seed: int = 20260703
) -> float:
    """AUC of a classifier trained on sensitive attributes only (5-fold OOF)."""
    if not _SKLEARN:
        raise RuntimeError("scikit-learn required for the bias baseline")
    from importlib import import_module  # noqa: PLC0415

    np = import_module("numpy")  # via importlib so mypy does not load numpy's stubs
    from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
    from sklearn.model_selection import StratifiedKFold  # noqa: PLC0415

    x = np.asarray(sensitive, dtype=float)
    y = np.asarray(labels, dtype=int)
    oof = np.zeros(len(y))
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    for tr, te in skf.split(x, y):
        clf = LogisticRegression(max_iter=2000)
        clf.fit(x[tr], y[tr])
        oof[te] = clf.predict_proba(x[te])[:, 1]
    return round(roc_auc(y.tolist(), oof.tolist()), 6)


def evaluate_bias_gate(
    model_auc: float | None,
    sensitive: list[list[float]] | None,
    labels: list[int] | None,
    sensitive_fields: list[str],
) -> dict[str, object]:
    """Return the PHASE0_BIAS_BASELINE artifact payload. Fail-closed by default."""
    if sensitive is None or labels is None or not sensitive_fields:
        return {
            "phase": "0",
            "baseline_type": "sensitive_attribute_only",
            "sensitive_fields_used": sensitive_fields,
            "model_auc": model_auc,
            "baseline_auc": None,
            "baseline_greater_or_equal": None,
            "release_blocked": True,
            "reason": "sensitive metadata unavailable; release blocked pending human-review record",
        }
    baseline = sensitive_only_auc(sensitive, labels)
    ge = model_auc is None or baseline >= model_auc
    return {
        "phase": "0",
        "baseline_type": "sensitive_attribute_only",
        "sensitive_fields_used": sensitive_fields,
        "model_auc": model_auc,
        "baseline_auc": baseline,
        "baseline_greater_or_equal": bool(ge),
        "release_blocked": bool(ge),
        "reason": (
            "bias baseline >= model AUC: performance may be demographic leakage"
            if ge
            else "bias baseline below model AUC"
        ),
    }
