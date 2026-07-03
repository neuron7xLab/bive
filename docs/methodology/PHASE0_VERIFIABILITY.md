# Phase 0 — Verbal Verifiability

**Objective.** Extract externally checkable claims and test, subject-independently,
whether verifiability features discriminate deceptive from truthful text with
honest calibration — without emitting any person-level verdict.

**Signal.** Verifiability Approach (Nahari, Vrij & Fisher 2014): truthful accounts
carry more checkable detail (named entities, numbers, times, places). Reported as
a review signal, never a deception score.

**Features** (`bive.cogveritas.verifiability_tagger`): `count_verifiable`,
`count_unverifiable`, `verifiability_ratio`, `detail_density`, `named_entity_count`,
`temporal_anchor_count`, `spatial_anchor_count`. Deterministic; optional spaCy
`en_core_web_trf` for entities with a deterministic fallback.

**Protocol.** StandardScaler + LogisticRegression, isotonic calibration,
`GroupKFold(5)` by hotel (Op-Spam) / clip (RLT). Metrics: AUC + bootstrap CI, ECE
and Brier before/after calibration, 10-bin reliability diagram.

**Kill criterion.** Calibrated subject-independent AUC ≤ 0.60 on both datasets →
Phase 1 blocked. One passes / one fails → blocked by default (see decision doc).

**Result.** Op-Spam 0.615 (ECE 0.015), RLT 0.554 → **Phase 1 BLOCKED**.
Reproduce: `python scripts/run_phase0_verifiability.py` then `make cogveritas-verify`.
