# Empirical Validation on Real Labeled Deception Data

BIVE's operating claims are backed by validation on **real, public, labeled
deception corpora** — not synthetic self-authored cases. The pipeline lives in
[`research/cogveritas/`](../research/cogveritas/) and is reproducible:

```bash
cd research/cogveritas && ./fetch_data.sh && python evaluate.py
```

## Method
Interpretable, cited verbal features — the **Verifiability Approach**
(Nahari/Vrij), **Reality Monitoring** (Johnson & Raye), and **Newman-Pennebaker
"Lying Words"** — scored per account, classified with a standardized,
isotonic-calibrated logistic model, evaluated with ROC-AUC / ECE / Brier and
bootstrap CIs. No black box; every feature's coefficient direction is inspected.

## Corpora
- **Ott et al. Deceptive Opinion Spam** (1,600 hotel reviews, 800 deceptive
  MTurk / 800 truthful web) — the field's gold standard.
- **Diplomacy** (Peskov et al., ACL 2020 — 3,557 game-negotiation messages,
  7.8% lies) — used only as an out-of-domain transfer test.

## Results (the honest law)
| Regime | ROC-AUC | ECE (calibration) |
|---|---|---|
| in-domain (Ott, 5-fold) | **0.75** [0.73–0.77] | **0.024** ✅ |
| cross-sub-domain (sentiment shift) | 0.60–0.72 | 0.18 ✗ |
| cross-corpus (Ott→Diplomacy) | 0.61 | 0.57 ✗✗ |

Controls: length-only baseline = 0.497 (chance) — the signal is not a length
artifact. TF-IDF bag-of-words ceiling = 0.955 AUC **but ECE 0.157** — an
uninterpretable, miscalibrated black box that captures lexical/topical leakage,
not deception constructs.

Construct validity: every coefficient matches the literature —
`first-person-singular → deceptive`, `spatial/temporal detail → truthful`
(Reality Monitoring), `exclusive words → truthful`.

## Leakage & bias audit (`research/cogveritas/leakage_audit.py`)
- **The TF-IDF "SOTA" is leakage.** Cross-corpus (Ott → Diplomacy) it collapses
  from 0.955 to **0.510 (chance)**; the interpretable model holds **0.601**. High
  accuracy that does not transfer is not a deception signal.
- **Shortcut probe (Mambreyan analogue).** Content-free style alone (punctuation,
  word length, stopword ratios) reaches **AUC 0.653** in-domain — much of Op-Spam
  separability is a source-style artifact, not deception. **Any headline ≥ 0.85
  is assumed leakage until cross-corpus proven.**

## What this means for the product
1. **Discrimination is real but modest** (~0.75 in-domain, ~0.61–0.72 out) and
   **degrades gracefully with domain distance**.
2. **Calibrated probabilities are only defensible in-domain.** Off the training
   distribution, calibration collapses (ECE 0.18–0.57). Therefore, cross-domain,
   BIVE surfaces **ordinal review flags, never probabilities** — an empirically
   forced rule, not a stylistic choice.
3. Any headline accuracy above this band (80–99% multimodal "SOTA", the 0.955
   TF-IDF ceiling) is dataset/lexical leakage, not a deception signal.
4. The correct product is therefore a **human-review evidence assistant** that
   surfaces cited construct flags and generates corroboration questions — which is
   exactly BIVE's non-negotiable no-verdict invariant, now backed by data.

Full write-up: [`research/cogveritas/PHASE0_REPORT.md`](../research/cogveritas/PHASE0_REPORT.md).
