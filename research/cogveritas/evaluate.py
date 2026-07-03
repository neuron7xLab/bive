"""Phase 0 validation: interpretable verbal features on a real labeled corpus.

Protocol (honest, pre-registered):
- Corpus: Ott et al. Deceptive Opinion Spam (1600 reviews, 800 deceptive MTurk /
  800 truthful Web). Positive class = deceptive (label 1).
- Split: stratified 5-fold CV (Ott's own protocol). NOTE: this is fold-CV, not
  author-independent; truthful reviews come from many web authors and deceptive
  from many Turkers, limiting leakage, but hotel identity can still leak. Stated
  as a limitation, not hidden.
- Model: standardized LogisticRegression (interpretable), isotonic-calibrated via
  nested CV (CalibratedClassifierCV) so probabilities are honest out-of-fold.
- Metrics on pooled out-of-fold predictions: ROC-AUC (+bootstrap CI), Brier, ECE,
  accuracy. Baselines: length-only, and a TF-IDF bag-of-words ceiling.
- KILL GATE: calibrated ROC-AUC <= 0.60 -> interpretable verbal content is not a
  viable basis; do not proceed to multimodal.
"""

from __future__ import annotations

import csv
import json
import sys

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import FEATURE_NAMES, vectorize

SEED = 20260703
KILL_AUC = 0.60
DATA = "data/opspam.csv"


def load() -> tuple[list[str], np.ndarray]:
    texts: list[str] = []
    labels: list[int] = []
    with open(DATA, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            texts.append(row["Ori_Review"])
            labels.append(1 if row["Label"] == "1" else 0)  # 1 = deceptive
    return texts, np.array(labels)


def ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1]) if i < bins - 1 else (p >= edges[i]) & (p <= edges[i + 1])
        if m.sum() == 0:
            continue
        total += (m.sum() / len(p)) * abs(p[m].mean() - y[m].mean())
    return float(total)


def bootstrap_auc(y: np.ndarray, p: np.ndarray, n: int = 2000, seed: int = SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    stats = []
    idx = np.arange(len(y))
    for _ in range(n):
        s = rng.choice(idx, len(idx), replace=True)
        if len(np.unique(y[s])) < 2:
            continue
        stats.append(roc_auc_score(y[s], p[s]))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(lo), float(hi)


def oof_predict(build_features, X_texts: list[str], y: np.ndarray, calibrated: bool = True) -> np.ndarray:
    """Pooled out-of-fold calibrated probabilities via stratified 5-fold CV."""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y))
    idx_all = np.arange(len(y))
    for tr, te in skf.split(idx_all, y):
        Xtr = build_features([X_texts[i] for i in tr])
        Xte = build_features([X_texts[i] for i in te])
        base = make_pipeline(StandardScaler(with_mean=not hasattr(Xtr, "tocsr")), LogisticRegression(max_iter=2000, C=1.0))
        if calibrated:
            clf = CalibratedClassifierCV(base, method="isotonic", cv=3)
        else:
            clf = base
        clf.fit(Xtr, y[tr])
        oof[te] = clf.predict_proba(Xte)[:, 1]
    return oof


def report(name: str, y: np.ndarray, p: np.ndarray) -> dict:
    auc = roc_auc_score(y, p)
    lo, hi = bootstrap_auc(y, p)
    acc = float(((p >= 0.5).astype(int) == y).mean())
    r = {
        "model": name,
        "roc_auc": round(auc, 4),
        "auc_ci95": [round(lo, 4), round(hi, 4)],
        "brier": round(brier_score_loss(y, p), 4),
        "ece": round(ece(y, p), 4),
        "accuracy": round(acc, 4),
    }
    print(f"{name:28} AUC={r['roc_auc']:.3f} [{lo:.3f}-{hi:.3f}]  ECE={r['ece']:.3f}  Brier={r['brier']:.3f}  acc={r['accuracy']:.3f}")
    return r


def main() -> int:
    texts, y = load()
    print(f"corpus: {len(y)} reviews, deceptive={int(y.sum())}, truthful={int((1 - y).sum())}\n")

    # 1) Interpretable science features (the system under test), calibrated.
    feat_matrix = lambda ts: np.array([vectorize(t) for t in ts])  # noqa: E731
    p_feat = oof_predict(feat_matrix, texts, y, calibrated=True)
    results = [report("verbal-science (calibrated)", y, p_feat)]

    # 2) Baseline: length-only (guards against a length artifact).
    len_only = lambda ts: np.array([[len(t.split())] for t in ts], dtype=float)  # noqa: E731
    results.append(report("baseline: length-only", y, oof_predict(len_only, texts, y, calibrated=True)))

    # 3) Ceiling reference: TF-IDF bag-of-words (Ott ~88%); NOT interpretable.
    #    Vectorizer must be fit on the train fold and applied to test (shared vocab).
    p_tfidf = np.zeros(len(y))
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for tr, te in skf.split(np.arange(len(y)), y):
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000)
        Xtr = vec.fit_transform([texts[i] for i in tr])
        Xte = vec.transform([texts[i] for i in te])
        clf = LogisticRegression(max_iter=2000, C=4.0)
        clf.fit(Xtr, y[tr])
        p_tfidf[te] = clf.predict_proba(Xte)[:, 1]
    results.append(report("ceiling: tf-idf 1-2gram", y, p_tfidf))

    # 4) Univariate direction check on the key construct (Verifiability Approach).
    verif = np.array([vectorize(t)[FEATURE_NAMES.index("verifiability_density")] for t in texts])
    corr = float(np.corrcoef(verif, y)[0, 1])
    print(f"\nVerifiability vs deceptive-label point-biserial r = {corr:+.3f} "
          f"({'truthful more verifiable (expected)' if corr < 0 else 'UNEXPECTED sign'})")

    # Kill gate.
    main_auc = results[0]["roc_auc"]
    verdict = "PASS" if main_auc > KILL_AUC else "KILL"
    print(f"\nKILL-GATE (AUC > {KILL_AUC}): {verdict}  (calibrated verbal-science AUC = {main_auc:.3f})")

    out = {
        "corpus": "Ott Deceptive Opinion Spam (1600)",
        "protocol": "stratified 5-fold CV, isotonic-calibrated logistic; positive=deceptive",
        "limitation": "fold-CV not author/hotel-independent; single-domain (hotel reviews)",
        "results": results,
        "verifiability_point_biserial_r": round(corr, 4),
        "kill_gate": {"threshold_auc": KILL_AUC, "verdict": verdict},
    }
    with open("phase0_results.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote phase0_results.json")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
