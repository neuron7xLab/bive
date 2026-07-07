# COGVERITAS Hard Level-Up Protocol

Status: execution protocol.
Mode: fail-closed.
Purpose: replace inflated self-assessment with external-standard scoring and a hard upgrade path.

## 1. External reference frame

This project is judged against external standards, not internal coherence.

Reference anchors:

- NIST AI RMF: govern, map, measure, manage; trustworthiness must be built into design, development, use, and evaluation.
- OpenAI Preparedness Framework: tracked risk categories, thresholds, scalable evaluations, safeguard reports, leadership review.
- Google DeepMind Frontier Safety Framework: critical capability levels, early warning evaluations, mitigation plans, periodic review.
- SWE-bench / SWE-rebench / SWE-MERA research: static benchmarks are contamination-prone; repo-level tasks need execution-based, fresh, reproducible evaluation.
- SWE-Effi: accuracy alone is insufficient; time, tokens, cost, and expensive failure modes must be measured.

## 2. Corrected current level

Do not score the repository as elite because it has fast PR velocity or green CI.

Current level estimate:

```text
Architecture discipline:        7.0 / 10
Risk governance:                6.5 / 10
Metric validity:                6.0 / 10
Cross-domain evidence:          5.5 / 10
CI/release discipline:          7.5 / 10
Product workflow:               7.0 / 10
Overclaim control:              7.5 / 10
Data/reproducibility maturity:  5.5 / 10
Overall:                        6.6 / 10
```

Interpretation:

```text
Strong prototype / early product-research system.
Not elite.
Not institution-grade.
Not yet benchmark-grade.
```

## 3. Hard blockers

The project remains below elite level until these are closed:

1. No independent external replication.
2. No benchmark card with contamination controls.
3. No cost/time/resource effectiveness report.
4. Dataset access is incomplete or partly substituted.
5. Claim segmentation is not yet proven at atomic span quality.
6. Open PR hygiene is weak if obsolete scaffold PRs remain open.
7. Scalable evaluation battery is not separated from ordinary CI.
8. UI/product claims are ahead of published external validation.
9. No formal threat model for misuse of analyst outputs.
10. No release-grade domain-distance policy enforced across every surface.

## 4. Aggressive upgrade tracks

### Track A — Measurement truth

Deliverables:

- `artifacts/verification/BENCHMARK_CARD.json`
- `artifacts/verification/CONTAMINATION_AUDIT.json`
- `artifacts/verification/CROSS_DOMAIN_MATRIX.json`

Done:

- every reported number has dataset, split, group key, CI, calibration, and leakage note.
- no headline metric exists without a limitation field.

Gate:

```text
MEASUREMENT_TRUTH_PASS
```

### Track B — Atomic evidence quality

Deliverables:

- atomic claim span fixtures,
- `CLAIM_SEGMENTATION_QUALITY.json`,
- no orphan claims,
- deterministic claim ids.

Done:

- span preservation >= 0.95,
- id stability = 1.0,
- orphan claim rate = 0.

Gate:

```text
ATOMIC_EVIDENCE_PASS
```

### Track C — Domain-distance enforcement

Deliverables:

- domain taxonomy,
- in-domain / adjacent / out-of-domain policy,
- probability suppression outside validated regime.

Done:

- cross-domain outputs are ordinal-only unless calibration is demonstrated.
- every output states its allowed-use regime.

Gate:

```text
DOMAIN_DISTANCE_PASS
```

### Track D — Resource-effectiveness audit

Deliverables:

- runtime cost report,
- token/compute estimate for agent runs,
- expensive-failure log,
- regression budget.

Done:

- every release reports accuracy, time, cost, and failure mode.
- no gate can spend unlimited resources silently.

Gate:

```text
RESOURCE_EFFECTIVENESS_PASS
```

### Track E — Product claim audit

Deliverables:

- README/docs/UI/API/package metadata scanner,
- forbidden overclaim registry,
- release claim artifact.

Done:

- no unsupported capability claim survives release.
- product language is weaker than the evidence, never stronger.

Gate:

```text
PRODUCT_CLAIM_AUDIT_PASS
```

### Track F — External replication package

Deliverables:

- one-command reproduction script,
- dataset access notes,
- container or lockfile evidence,
- independent reviewer checklist.

Done:

- a fresh machine can reproduce the reported artifacts.
- missing external data produces a blocked state, not success.

Gate:

```text
EXTERNAL_REPLICATION_READY
```

## 5. New score thresholds

```text
< 6.0  = unstable prototype
6.0-7.0 = strong internal research prototype
7.0-8.0 = credible product-research system
8.0-9.0 = institution-grade engineering candidate
9.0+   = externally replicated, benchmark-grade, release-disciplined system
```

COGVERITAS is currently in the 6.5-7.0 band.

To reach 8.0:

- close obsolete PRs,
- harden gates,
- enforce domain-distance policy,
- add benchmark/contamination cards,
- produce reproducible external package.

To reach 9.0:

- external replication,
- fresh benchmark tasks,
- resource-effectiveness reporting,
- independent review,
- formal misuse/threat model,
- release claim audit enforced in CI.

## 6. Immediate PR order

1. Close obsolete scaffold/protocol PRs or merge only if rebased and useful.
2. Merge active product PR only after CI is fully green.
3. Add Benchmark Card + Contamination Audit.
4. Add Domain Distance Policy gate.
5. Add Resource Effectiveness Audit.
6. Add Product Claim Audit.
7. Add External Replication package.

## 7. Final command

```bash
make cogveritas-verify
make verify-release
make benchmark-card-check
make contamination-audit
make domain-distance-check
make resource-effectiveness-check
make product-claim-audit
```

Final valid state:

```text
COGVERITAS_VERIFY_COMPLETE
VERIFY_RELEASE_PASS
MEASUREMENT_TRUTH_PASS
ATOMIC_EVIDENCE_PASS
DOMAIN_DISTANCE_PASS
RESOURCE_EFFECTIVENESS_PASS
PRODUCT_CLAIM_AUDIT_PASS
EXTERNAL_REPLICATION_READY
```
