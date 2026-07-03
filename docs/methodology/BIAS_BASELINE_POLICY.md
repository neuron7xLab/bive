# Bias Baseline Policy (Mambreyan gate)

If a classifier trained on a sensitive attribute alone (e.g. gender) matches or
beats the real model, the model's "accuracy" is demographic leakage, not the
intended verifiability signal — and release is blocked.

- `baseline_auc >= model_auc` → `release_blocked = true`.
- Sensitive metadata unavailable → the gate does **not** silently pass;
  `release_blocked = true` pending an explicit human-review record.
- Artifact: `artifacts/verification/PHASE0_BIAS_BASELINE.json`. Missing → FAIL.

The current text corpora (Op-Spam, RLT transcripts) carry no committed sensitive
metadata, so the Phase 0 bias gate is `release_blocked = true` by design.
