# Domain-Distance Policy

Implements the policy half of PR-2. Enforced by `scripts/domain_distance_check.py`
(`DOMAIN_DISTANCE_PASS`), which writes `artifacts/verification/DOMAIN_DISTANCE_POLICY.json`.

## Rule

An in-domain metric is never a general-capability claim. Output is gated by domain
regime, and **probability is suppressed outside the calibrated in-domain regime**.

| Regime | Calibrated | Allowed output |
|---|---|---|
| in-domain (calibrated, ECE < 0.10 demonstrated) | yes | ordinal flags; calibrated probability allowed |
| cross-corpus | no | ordinal-only |
| cross-domain / high-stakes / unknown | no | ordinal-only |

## Enforcement (runtime, not just documentation)

The live service is Phase 0: cross-domain calibration is not demonstrated, so the
output contract emits **no calibrated probability at all** — `calibrated_probability`
is `null` in every response. The gate verifies this at runtime (analyses a sample and
asserts probability is suppressed), so the policy cannot drift from behaviour.

Invariants this policy upholds:

```text
unknown domain = ordinal-only output
unsupported probability = suppressed
verdict = null
```

## Basis

See `CROSS_DOMAIN_MATRIX.md`: every regime except in-domain sits at or near chance.
Emitting a probability there would be an unsupported claim.
