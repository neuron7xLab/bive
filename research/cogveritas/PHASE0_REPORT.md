# COGVERITAS — Phase 0: Verbal Baseline on Real Labeled Deception Data

**Date:** 2026-07-03 · **Status:** KILL-GATE PASSED · **Reproduce:** `python evaluate.py`

## Question (pre-registered)
Can *interpretable, causally-grounded verbal features* — the Verifiability Approach,
Reality Monitoring, and Newman-Pennebaker "Lying Words" — discriminate deceptive
from truthful text on a **real labeled corpus**, with **honest calibration**, above
a kill threshold of AUC 0.60? If not, verbal content alone is not a viable basis
and multimodal work is not warranted.

## Data
Ott et al. (2011/2013) **Deceptive Opinion Spam Corpus** — 1,600 hotel reviews,
800 deceptive (Amazon MTurk) / 800 truthful (TripAdvisor/Expedia/…), balanced
50/50 by sentiment. Gold-standard, publicly available. Positive class = deceptive.

## Protocol
- Stratified **5-fold cross-validation** (Ott's own protocol), seed fixed.
- **14 interpretable features** (densities of verifiable detail, perceptual /
  spatial / temporal detail, cognitive operations, first-person sing./plur.,
  exclusive words, emotion, superlatives, motion, lexical diversity, sentence
  length, word count). No black box.
- Standardized **logistic regression**, **isotonic-calibrated** via nested CV, so
  reported probabilities are honest out-of-fold.
- Metrics on pooled out-of-fold predictions: ROC-AUC (+ 2000× bootstrap 95% CI),
  ECE (10-bin), Brier, accuracy.
- Baselines: **length-only** (artifact guard) and **TF-IDF 1–2gram** (uninterpretable ceiling).

## Results

| Model | ROC-AUC [95% CI] | ECE | Brier | Acc | Interpretable |
|---|---|---|---|---|---|
| **verbal-science (calibrated)** | **0.751 [0.727–0.774]** | **0.024** | 0.203 | 0.688 | ✅ |
| length-only baseline | 0.497 [0.469–0.524] | 0.041 | 0.253 | 0.500 | — |
| TF-IDF 1–2gram (ceiling) | 0.955 [0.945–0.963] | 0.157 | 0.109 | 0.890 | ❌ |

- **Kill-gate: PASS** (0.751 > 0.60).
- **Not a length artifact** — length alone is at chance (0.497).
- **Calibration is genuinely good** — ECE 0.024 (< 0.05 target); probabilities mean what they say.
- **Construct validity confirmed** — verifiability_density vs deceptive label
  point-biserial r = **−0.137** (truth-tellers more verifiable, as theory predicts).

## Interpretability (standardized LR coefficients, all directions match theory)
| Feature | Coef | Direction | Literature |
|---|---|---|---|
| first_singular_density | +0.72 | → deceptive | Newman-Pennebaker (and this dataset's own finding) |
| spatial_density | −0.51 | → truthful | Reality Monitoring |
| temporal_density | −0.42 | → truthful | Reality Monitoring |
| exclusive_density | −0.22 | → truthful | cognitive complexity (Lying Words) |
| cognitive_ops_density | +0.18 | → deceptive | Reality Monitoring (internally generated) |
| pos_superlative_density | +0.17 | → deceptive | imagination/exaggeration |
| lexical_diversity | −0.17 | → truthful | cognitive load |

## Honest interpretation
1. Causally-grounded verbal constructs give **modest but real, well-calibrated**
   discrimination (0.75). This is a legitimate, publishable-strength result for
   *interpretable* deception screening — and unlike the ceiling, it says what it does.
2. The **TF-IDF ceiling (0.955)** is a black box: high accuracy but ECE 0.157
   (miscalibrated) and no construct-level meaning. It captures topical/lexical
   surface patterns that will not transfer across domains and cannot be defended
   to an analyst. High accuracy here is a warning sign, not a goal.
3. Every feature's sign matches the peer-reviewed literature — the model is not
   just accurate, it is **mechanistically coherent**.

## Limitations (stated, not hidden)
- **Fold-CV, not author/hotel-independent**: the same hotel can appear in train and
  test. Cross-domain/subject-independent AUC will be **lower** — likely 0.65–0.70.
- **Single domain** (hotel reviews) and **English-only**.
- Deceptive class is *instructed lying* (MTurk), not high-stakes real deception.

## Phase 1a — generalization under distribution shift (cross-sentiment)
Train on one review polarity, test on the other (a real distribution shift with
the sentiment confound made explicit):

| Shift | ROC-AUC | ECE | Acc |
|---|---|---|---|
| train POS → test NEG | 0.600 | 0.204 | 0.550 |
| train NEG → test POS | 0.721 | 0.178 | 0.626 |

**Findings (honest):**
1. In-domain AUC 0.75 drops to **0.60–0.72** under shift — the higher figure is
   optimistic, confirming the audit's warning.
2. **Calibration does NOT transfer**: ECE jumps from 0.024 (in-domain) to
   0.18–0.20 under shift. The calibrated probabilities are *not* trustworthy off
   the training distribution.
3. Part of the signal is entangled with sentiment (POS→NEG is worst).

**Consequence (design rule):** cross-distribution, the system must emit **ordinal
review flags, not probabilities**. Percentages are only defensible in-domain,
where ECE < 0.05 was demonstrated. This is now a hard product rule, not a caveat.

## Verdict
Interpretable, causally-grounded verbal features are a **legitimate in-domain
screening signal** (AUC 0.75, ECE 0.024, every construct matching theory) that
**degrades to 0.60–0.72 with broken calibration under distribution shift**. That
is the true ceiling of passive verbal deception screening — modest, honest, and
useful only as a human-review aid. Any claim above this is dataset leakage.

## Phase 2 — cross-corpus (extreme domain shift)
Train on Op-Spam (hotel reviews), **zero-shot test on the Diplomacy deception
dataset** (Peskov et al., ACL 2020 — game-negotiation messages, 3,557 messages,
7.8% lies). Radically different genre, base rate and register.

| Metric | Value | Reference |
|---|---|---|
| ROC-AUC | **0.609** | chance = 0.500 |
| PR-AUC | 0.100 | base rate = 0.078 |
| ECE | 0.567 | (catastrophic) |

**Findings:** discrimination **partially transfers** (0.609 > chance) — the causal
constructs carry *some* cross-domain signal, which pure lexical leakage would not
(a TF-IDF model would collapse to chance here). But **calibration is destroyed**
(ECE 0.567): probabilities fitted on one domain are meaningless on another.

## Synthesis — the empirical law
| Regime | Discrimination (AUC) | Calibration (ECE) |
|---|---|---|
| in-domain (5-fold) | **0.75** | **0.024** ✅ |
| cross-sub-domain (sentiment) | 0.60–0.72 | 0.18 ✗ |
| cross-corpus (extreme) | 0.61 | 0.57 ✗✗ |

**Discrimination degrades gracefully with domain distance (0.75 → 0.70 → 0.61);
calibration collapses immediately off-distribution.** This is the honest ceiling
of passive verbal deception screening.

## Phase 3 — leakage & bias audit (`leakage_audit.py`)
The audit's #1 discipline: *treat any AUC ≥ 0.85 as a bug until proven otherwise.*

**Test 1 — does the TF-IDF "SOTA" transfer cross-corpus?**
| Model | in-domain | cross-corpus (→ Diplomacy) |
|---|---|---|
| TF-IDF 1–2gram | 0.955 | **0.510 (chance)** |
| verbal-science | 0.75 | **0.601** |
The 0.955 "SOTA" **collapses to pure chance** off-domain — it learned Op-Spam's
lexical/topical surface (hotel vocabulary, MTurk register), not deception. The
interpretable model **retains above-chance signal** (0.601). High accuracy that
does not transfer is leakage, not a deception detector.

**Test 2 — Mambreyan-analog shortcut.** Content-free style features (punctuation,
word length, uppercase and stopword ratios — *zero* deception meaning) alone
reach **AUC 0.653** in-domain. So a large share of any Op-Spam classifier's
in-domain score is a **source-style shortcut** (MTurk vs web authors write
differently), not deception. This is the text analogue of Mambreyan et al.'s
sex-only classifier matching multimodal "SOTA" on the Real-Life Trial data.

**Consequence:** in-domain deception numbers are inflated by source artifacts; the
only signal that survives off-domain is the modest (~0.60) interpretable-construct
transfer. Any headline ≥ 0.85 must be assumed leakage until cross-corpus proven.

## Final verdict (empirical ground truth)
1. Interpretable, causally-grounded verbal features are a **real, mechanistically
   coherent** deception-screening signal — but a **modest** one (~0.75 in-domain,
   ~0.61–0.72 out-of-domain).
2. **Honest probabilities are only defensible in-domain** (ECE 0.024). Off the
   training distribution the system must emit **ordinal review flags, not
   percentages** — a hard product rule, now empirically forced.
3. Any reported accuracy above this band (e.g. the 0.955 TF-IDF ceiling, or the
   80–99% multimodal "SOTA") is dataset/lexical leakage, not deception signal —
   exactly as the audit warned.
4. Therefore the correct product is a **human-review evidence assistant** that
   surfaces cited construct flags and generates corroboration questions — never a
   lie detector. This is precisely bive's existing invariant, now backed by data.
