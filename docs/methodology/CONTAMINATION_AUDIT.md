# Contamination Audit

Implements the contamination-control half of PR-1. Enforced by
`scripts/contamination_audit.py` (`CONTAMINATION_AUDIT_PASS`), which writes the
machine-readable `artifacts/verification/CONTAMINATION_AUDIT.json`.

## Rule

> Any headline ROC-AUC ≥ 0.85 is assumed to be leakage until proven to transfer
> cross-corpus.

A high number is not a capability until it survives a domain shift. The audit
**blocks the release** if a high headline is presented without a leakage / ceiling /
cross-corpus qualifier.

## What is checked

1. **Frozen result** (`research/cogveritas/phase0_results.json`): any model with
   AUC ≥ 0.85 must be labelled a `ceiling` / `tf-idf` / `leakage` row — never a
   headline capability. (The real TF-IDF 1–2gram row is 0.9548 and is so labelled.)
2. **Documentation** (`EMPIRICAL_VALIDATION.md`, `BENCHMARK_CARD.md`,
   `PHASE0_REPORT.md`): any AUC-like number ≥ 0.85 in prose must have a
   leakage / cross-corpus / collapse qualifier within its surrounding context.

## Evidence of contamination (why the rule exists)

The TF-IDF ceiling reaches **0.9548** in-domain but collapses to **0.510 (chance)**
cross-corpus (Ott → Diplomacy). High accuracy that does not transfer is lexical /
topical leakage, not a deception signal. This is the empirical basis for the
no-verdict invariant and the domain-distance policy.

## Artifact

`artifacts/verification/CONTAMINATION_AUDIT.json` records the leakage threshold, the
surfaces scanned, and any violations. A missing artifact fails the gate.
