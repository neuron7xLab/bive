# Decision: Phase 0 dataset divergence

**Context.** The spec names MU3D and Op-Spam. MU3D requires interactive
registration and cannot be fetched non-interactively in this environment.

**Decision.** Emit the MU3D manifest as `unavailable` (fail-closed) and use the
**Real-Life Trial** corpus (Pérez-Rosas 2015) as the second real dataset. RLT is
real high-stakes deception — a stronger test than MU3D's social lies.

**Outcome (fail-closed, honest).** Subject-independent verifiability-only AUC:
Op-Spam `0.615` (hotel-independent, passes kill > 0.60), RLT `0.554` (fails,
95% CI includes chance). Because one dataset passes and one fails, **Phase 1
remains BLOCKED** — the correct, data-forced result. This matches the empirical
law in `../EMPIRICAL_VALIDATION.md`: verbal cues do not detect real high-stakes
deception.

**Review required** before unlocking Phase 1: obtain MU3D (or an equivalent
second high-stakes corpus) and re-run; Phase 1 unlocks only if both clear 0.60.
