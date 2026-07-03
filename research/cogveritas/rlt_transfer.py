"""Phase 4 — the decisive test: REAL high-stakes deception (Real-Life Trial).

Op-Spam is low-stakes *instructed* lying (MTurk reviews). The Real-Life Trial
corpus (Perez-Rosas et al. 2015; 61 deceptive / 60 truthful courtroom transcripts,
labelled by verdict) is *real high-stakes* deception — the field gold standard.

Tests:
  1. RLT in-domain (5-fold): do interpretable constructs work on real deception?
  2. Op-Spam -> RLT transfer: does anything learned on reviews carry to court?
  3. Does the TF-IDF "SOTA" transfer to real deception, or is it a review artifact?

Run: ./fetch_data.sh && python rlt_transfer.py
"""

from __future__ import annotations

import csv
import glob

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import vectorize

SEED = 20260703


def _read(pattern: str) -> list[str]:
    return [open(f, encoding="utf-8", errors="replace").read() for f in sorted(glob.glob(pattern))]


def load_rlt() -> tuple[list[str], np.ndarray]:
    dec = _read("data/rlt/Deceptive/*.txt")
    tru = _read("data/rlt/Truthful/*.txt")
    return dec + tru, np.array([1] * len(dec) + [0] * len(tru))


def load_opspam() -> tuple[list[str], np.ndarray]:
    rows = list(csv.DictReader(open("data/opspam.csv", encoding="utf-8", errors="replace")))
    return [r["Ori_Review"] for r in rows], np.array([1 if r["Label"] == "1" else 0 for r in rows])


def boot_ci(y: np.ndarray, p: np.ndarray, n: int = 2000) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    s = []
    for _ in range(n):
        i = rng.choice(len(y), len(y), replace=True)
        if len(np.unique(y[i])) > 1:
            s.append(roc_auc_score(y[i], p[i]))
    lo, hi = np.percentile(s, [2.5, 97.5])
    return float(lo), float(hi)


def cv_auc(x: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y))
    for tr, te in skf.split(x, y):
        c = make_pipeline(StandardScaler(with_mean=not hasattr(x, "tocsr")), LogisticRegression(max_iter=2000))
        c.fit(x[tr], y[tr])
        oof[te] = c.predict_proba(x[te])[:, 1]
    return float(roc_auc_score(y, oof)), oof


def main() -> int:
    rlt_txt, rlt_y = load_rlt()
    op_txt, op_y = load_opspam()
    xr = np.array([vectorize(t) for t in rlt_txt])

    print("RLT in-domain (real high-stakes deception, n=121, 5-fold):")
    a, oof = cv_auc(xr, rlt_y)
    lo, hi = boot_ci(rlt_y, oof)
    print(f"  verbal-science AUC = {a:.3f} [{lo:.3f}-{hi:.3f}]  (CI touching 0.5 = indistinguishable from chance)")

    print("\nOp-Spam (low-stakes) -> RLT (high-stakes) transfer:")
    vsc = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    vsc.fit(np.array([vectorize(t) for t in op_txt]), op_y)
    pr = vsc.predict_proba(xr)[:, 1]
    lo, hi = boot_ci(rlt_y, pr)
    print(f"  verbal-science AUC = {roc_auc_score(rlt_y, pr):.3f} [{lo:.3f}-{hi:.3f}]")
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    tf = LogisticRegression(max_iter=2000, C=4.0).fit(vec.fit_transform(op_txt), op_y)
    ptf = tf.predict_proba(vec.transform(rlt_txt))[:, 1]
    print(f"  TF-IDF 'SOTA'  AUC = {roc_auc_score(rlt_y, ptf):.3f}  (0.955 on reviews -> chance on real deception)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
