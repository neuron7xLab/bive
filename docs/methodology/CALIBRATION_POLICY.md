# Calibration Policy

A probability is emitted only when calibration is demonstrated. Otherwise the
system degrades to ordinal flags — never a percentage that means nothing.

- Metric: Expected Calibration Error (ECE), 10 bins, on subject-independent
  out-of-fold predictions, plus Brier and a reliability diagram.
- Threshold: `ECE < 0.10`. If `ECE >= 0.10`, `calibrated_probability = None`.
- Calibrator: isotonic (nested CV). Discrimination reported with a seeded
  bootstrap 95% CI.
- Phase 0 sets `float_probability_allowed = false`: even where in-domain ECE is
  low, cross-domain calibration is not demonstrated, so no probability is shipped
  until a phase clears the gate on held-out corpora.

Gate: `make calibration-gate` (this repo's construct gate) and the Phase 0
`calibration-ece` gate both fail closed on a missing artifact.
