# External Replication Attestation Protocol

## Why this exists

BIVE's institutional scorecard caps the project below *benchmark-grade* until a real,
independent replication of its one anchored empirical claim is recorded. This is the
correct posture: a repository cannot certify its own third-party replication. But an
honest cap still needs an honest *path* — otherwise "benchmark-grade" is unreachable by
construction, and the cap is decoration rather than a standard.

This protocol defines that path, and defines it so the target repository cannot forge it.

## The claim under replication

The frozen, pre-registered result — [`research/cogveritas/phase0_results.json`](../../research/cogveritas/phase0_results.json),
integrity-pinned by [`phase0_provenance.json`](../../research/cogveritas/phase0_provenance.json):

- **Corpus**: Ott et al. Deceptive Opinion Spam (1,600; public).
- **Protocol**: stratified 5-fold CV, isotonic nested-CV calibration, seed fixed.
- **Headline**: interpretable verbal-science features, ROC-AUC ≈ 0.751 (95% CI [0.727, 0.774]),
  ECE ≈ 0.024, above the AUC 0.60 kill threshold.

A replication reproduces this claim iff its reported headline AUC falls **within that 95%
confidence interval** and clears the kill threshold.

## How to attest

1. Fetch the public corpus (`research/cogveritas/fetch_data.sh`) and run the documented
   pipeline (`research/cogveritas/evaluate.py`) in your own environment.
2. Write an attestation JSON conforming to
   [`schemas/external_replication_attestation.schema.json`](../../schemas/external_replication_attestation.schema.json)
   and open a PR adding it under `research/cogveritas/replications/`.
3. Set `attester_class` honestly:
   - `independent` — you are **not** `neuron7xLab/bive` or its automation. Only these lift the cap.
   - `self` — the repo's own maintainers/CI reproducing from scratch. A witness, never a third-party attestation.
4. Include a `public_evidence_url` — a CI run, notebook, or log an auditor can open.

## What the gate re-derives (and what it cannot)

`scripts/external_replication_attest_check.py` **re-derives**, never trusts:

- the reported AUC reproduces the pre-registered value within its 95% CI;
- the reported model is the pre-registered headline;
- the AUC clears the kill threshold;
- an `independent` attester is not the canonical repository;
- a public evidence URL is present.

A malformed, self-issued-as-independent, or non-reproducing attestation **fails the gate**
(exit 1) — a false replication claim is surfaced, not silently ignored. Absence of any
attestation is the honest default (`attested: false`, cap in force), not a failure.

**Trust boundary (stated, not hidden).** The gate cannot fetch the evidence URL or verify a
cryptographic signature — there is no signing authority in an OSS repo. Machine-checkable:
independence, result-within-CI, structure. Human-checkable: the public evidence URL. The
gate is therefore *necessary but not sufficient* — it makes an unreproducible or
self-issued claim impossible to pass, while the final trust anchor remains a maintainer
following the public evidence. That honest limitation is the point: the cap lifts only on
evidence the repository did not, and could not, manufacture alone.
