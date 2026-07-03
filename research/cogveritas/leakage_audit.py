"""Phase 3 — leakage & bias audit (the audit's #1 discipline).

'Treat any AUC >= 0.85 as a bug until proven otherwise.' Two probes:

  Test 1 — Does the high-accuracy TF-IDF 'SOTA' TRANSFER cross-corpus? If it
  collapses to chance while the interpretable model holds, the SOTA was lexical
  leakage, not a deception signal.

  Test 2 — Mambreyan-analog shortcut: can CONTENT-FREE style (punctuation, word
  length, stopword ratios — nothing to do with deception) separate the classes?
  If so, the corpus is gameable by source artifacts, and much of any classifier's
  in-domain score is shortcut, not deception.

Run: ./fetch_data.sh && python leakage_audit.py
"""

from __future__ import annotations

import csv
import json
import re

import numpy as np
from features import vectorize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 20260703
STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
        "that", "this", "is", "are", "was", "i", "we", "you", "it"}


def load_opspam() -> tuple[list[str], np.ndarray]:
    rows = list(csv.DictReader(open("data/opspam.csv", encoding="utf-8", errors="replace")))
    return [r["Ori_Review"] for r in rows], np.array([1 if r["Label"] == "1" else 0 for r in rows])


def load_diplomacy() -> tuple[list[str], np.ndarray]:
    texts: list[str] = []
    labels: list[int] = []
    for fn in ("data/diplomacy_test.jsonl", "data/diplomacy_validation.jsonl"):
        for line in open(fn):
            d = json.loads(line)
            for m, lab in zip(d["messages"], d["sender_labels"], strict=False):
                if lab in (True, False) and len(m.split()) >= 5:
                    texts.append(m)
                    labels.append(0 if lab is True else 1)
    return texts, np.array(labels)


def shortcut_features(text: str) -> list[float]:
    n = len(text.split()) or 1
    toks = re.findall(r"[a-z']+", text.lower())
    return [
        text.count("!") / n,
        text.count(",") / n,
        text.count(".") / n,
        float(np.mean([len(w) for w in toks])) if toks else 0.0,
        sum(c.isupper() for c in text) / max(len(text), 1),
        sum(w in STOP for w in toks) / max(len(toks), 1),
    ]


def cv_auc(x: np.ndarray, y: np.ndarray) -> float:
    skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y))
    for tr, te in skf.split(x, y):
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        clf.fit(x[tr], y[tr])
        oof[te] = clf.predict_proba(x[te])[:, 1]
    return float(roc_auc_score(y, oof))


def main() -> int:
    texts, y = load_opspam()
    dtexts, dy = load_diplomacy()

    print("Test 1 — cross-corpus transfer (does SOTA survive off-domain?):")
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000)
    tfidf = LogisticRegression(max_iter=2000, C=4.0).fit(vec.fit_transform(texts), y)
    p_tfidf = tfidf.predict_proba(vec.transform(dtexts))[:, 1]
    print(f"  TF-IDF          in-domain 0.955 -> cross-corpus {roc_auc_score(dy, p_tfidf):.3f}")
    verbal = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    verbal.fit(np.array([vectorize(t) for t in texts]), y)
    p_verbal = verbal.predict_proba(np.array([vectorize(t) for t in dtexts]))[:, 1]
    print(f"  verbal-science  in-domain 0.75  -> cross-corpus {roc_auc_score(dy, p_verbal):.3f}")

    print("\nTest 2 — content-free style shortcut (no deception meaning):")
    xs = np.array([shortcut_features(t) for t in texts])
    print(f"  shortcut in-domain AUC = {cv_auc(xs, y):.3f}  (>>0.6 => corpus gameable by artifacts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
