# Cross-Domain Matrix

Implements the cross-domain half of PR-2. Enforced by
`scripts/cross_domain_matrix_check.py` (`CROSS_DOMAIN_MATRIX_PASS`), which validates
the frozen matrix `research/cogveritas/cross_domain_matrix.json` and writes
`artifacts/verification/CROSS_DOMAIN_MATRIX.json`.

The matrix makes cross-domain uncertainty **visible**: performance is recorded per
train→test pair, and the gate refuses any cross-domain cell that claims performance
at or above its in-domain counterpart (degradation must be honest).

## Frozen cells (verbal-science, unless noted)

| train → test | regime | ROC-AUC | calibrated |
|---|---|---|---|
| Ott → Ott | in-domain | 0.7507 | yes |
| Ott → Diplomacy | cross-corpus | 0.61 | no |
| Ott → RLT | cross-domain high-stakes | 0.548 (chance) | no |
| RLT → RLT | in-domain high-stakes | 0.562 (CI straddles chance) | no |
| tf-idf-ceiling: Ott → Ott | in-domain | 0.9548 | no |
| tf-idf-ceiling: Ott → Diplomacy | cross-corpus | **0.510 (chance)** | no |

## What the gate enforces

1. Every model's cross-domain cells are ≤ its in-domain cell (no cross-domain
   over-claim).
2. The required regimes are present, including the real high-stakes (RLT) regime.
3. The TF-IDF ceiling collapses into the chance band cross-corpus (the leakage proof).
4. The in-domain headline matches the frozen `phase0_results.json`.

## Meaning

Only the in-domain regime is calibrated. Every other cell is at or near chance and
is not a capability. This is the evidence base for the domain-distance policy
(probabilities suppressed outside calibrated in-domain) and the no-verdict invariant.
