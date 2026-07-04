# Institutional Scorecard

Implements the mandate's PR-7 (scorecard half). Computed by
`scripts/institutional_scorecard.py` (`INSTITUTIONAL_SCORECARD_PASS`), which writes
`artifacts/verification/INSTITUTIONAL_SCORECARD.json`.

Maturity is **not asserted** — it is *derived* from executable gates. There is no
manual override field and no way to raise the score except by making gates pass.
This is hierarchical inference over evidence: leaf gates → weighted dimensions →
score → band → institutional verdict.

## Weighted dimensions

| dimension | weight | source gates |
|---|---|---|
| architecture_discipline | 10 | capability-registry + dependency-contracts |
| risk_governance | 15 | misuse threat model + release governance |
| metric_validity | 15 | benchmark card + contamination audit |
| cross_domain_evidence | 10 | cross-domain matrix + domain-distance |
| ci_release_discipline | 10 | verify-release status |
| data_reproducibility | 15 | external replication |
| resource_effectiveness | 10 | resource-effectiveness |
| product_claim_control | 15 | product-claim audit |

`score = Σ (weight × fraction_of_source_gates_passing) / 10` → 0–10.

## Maturity bands

```
0–5.9   prototype
6.0–6.9 strong internal research prototype
7.0–7.9 credible product-research system
8.0–8.9 institution-grade candidate
9.0–10  externally replicated benchmark-grade system
```

## The honesty cap (why the score cannot lie)

The top band requires an **actual third-party replication**, which the repository
cannot self-certify — the external-replication gate only proves the package is
*ready*. So the band is **capped at 8.9 (institution-grade candidate)** until a real
external replication is recorded (`externally_replicated: false`). Even with every
gate green (raw score 10.0), the reported maturity is *institution-grade candidate*,
not benchmark-grade. This makes false maturity impossible: the score can only rise as
high as the evidence permits, and the last band is reserved for evidence this
repository cannot produce about itself.
