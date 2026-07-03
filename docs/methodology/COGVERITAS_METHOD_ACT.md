# COGVERITAS Method Act

COGVERITAS is **not a lie detector**. It is a fail-closed evidence-review system
that forces every claim onto an external-fact verification path:

```
claim → external checkability → provenance → calibration → bias audit → corroboration → no verdict
```

## Required scientific basis
1. **DePaulo et al. (2003), _Psychological Bulletin_ 129(1):74–118.** 158 cues,
   median behavioral cue effect ≈ `d = 0.10`. Most signals are noise.
2. **Luke (2019), _Perspectives on Psychological Science_ 14(4):646–671.** Even
   reported cue effects are inflated by publication bias and low power.
3. **Bond & DePaulo (2006), _PSPR_ 10(3):214–234.** Human accuracy ≈ 54% across
   24,483 judges.
4. **Mambreyan, Punskaya & Gunes (2022), ICPR.** Bias masquerades as accuracy;
   a sensitive-attribute-only classifier can match claimed SOTA.

These are reproduced empirically in this repository — see
[`../EMPIRICAL_VALIDATION.md`](../EMPIRICAL_VALIDATION.md): the interpretable
verbal signal is ~0.61 subject-independent on low-stakes reviews and **at chance
on the real high-stakes Real-Life Trial corpus**; the TF-IDF "SOTA" collapses
from 0.955 to chance cross-corpus.

## Operational conclusion
The task is **not** `detect lying`. The task is `force claims onto externally
checkable facts`. Internal linguistic coherence is not evidence. A polished
narrative is not evidence. A high score without calibration is not evidence. A
green CI without a metric artifact is invalid.

## Hardcoded invariants (release blockers)
- `verdict = None`, always (enforced in `bive.cogveritas.output_contract`).
- `calibrated_probability = None` if post-calibration `ECE >= 0.10`.
- Phase 1 stays **BLOCKED** unless calibrated subject-independent AUC `> 0.60` on
  **both** required datasets.
- Release **BLOCKED** if the sensitive-attribute-only baseline AUC `>=` model AUC,
  or if the bias artifact is unavailable.
- Missing artifact = FAIL. A green CI without a metric artifact is invalid.
- Forbidden person-level strings (`liar`, `guilty`, `lie detected`, …) may never
  appear in an output surface.

Verify with `make cogveritas-verify` (terminal contract ends in `⊛`).
