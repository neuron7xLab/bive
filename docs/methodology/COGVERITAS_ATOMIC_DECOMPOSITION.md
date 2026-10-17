# COGVERITAS Atomic Decomposition Protocol

Status: execution protocol.
Mode: fail-closed.
Purpose: decompose the elite-quality direction into atomic tasks. Each task has an input, output, and completion criterion.

## Decomposition Law

A task is valid only if it has:

```text
input -> transform -> output -> done criterion -> gate
```

If any field is missing, the task is not executable.

## Global Completion Contract

```text
make cogveritas-verify
make verify-release
```

The work is complete only when both commands pass or when the protocol explicitly records a blocked state with a reason and no unsupported product claim is emitted.

---

# Track A — Atomic Claim Segmentation

## A1. Span-preserving sentence normalization

Input:
- raw transcript text
- current normalizer

Transform:
- normalize whitespace
- preserve original character offsets
- preserve sentence boundary mapping

Output:
- normalized text
- offset map

Done criterion:
- every normalized sentence maps back to original text span
- no content loss on fixture set

Gate:
- `CLAIM_SPAN_PRESERVATION_PASS`

## A2. Atomic claim splitter

Input:
- sentence text
- offset map

Transform:
- split compound statements into atomic claims
- use deterministic rules first
- optional NLP parser only as enhancement

Output:
- list of atomic claims
- stable claim ids
- original span per claim

Done criterion:
- fixture set shows stable claim count and stable ids
- one sentence may produce multiple claims
- original sentence remains recoverable

Gate:
- `ATOMIC_CLAIM_SPLIT_PASS`

## A3. Claim provenance node upgrade

Input:
- atomic claims
- source transcript metadata

Transform:
- attach source id, sentence id, span, extractor version, feature schema hash

Output:
- provenance node per claim

Done criterion:
- every claim has source, span, extractor, hash
- no orphan claim exists

Gate:
- `CLAIM_PROVENANCE_COMPLETE`

## A4. Claim segmentation quality artifact

Input:
- claim fixtures
- segmentation output

Transform:
- compute preservation rate, deterministic-id stability, orphan rate

Output:
- `artifacts/verification/CLAIM_SEGMENTATION_QUALITY.json`

Done criterion:
- span preservation >= 0.95
- orphan rate = 0
- deterministic id stability = 1.0

Gate:
- `CLAIM_SEGMENTATION_QUALITY_PASS`

---

# Track B — Dataset Cards and Data Provenance

## B1. Dataset card schema

Input:
- current dataset manifests

Transform:
- define required fields for every dataset card

Output:
- `schemas/cogveritas/dataset_card.schema.json`

Done criterion:
- schema validates every committed dataset card

Gate:
- `DATASET_CARD_SCHEMA_PASS`

## B2. Dataset cards

Input:
- OP_SPAM manifest
- MU3D manifest
- RLT substitution record
- empirical validation report

Transform:
- create dataset cards with source, access, license, label schema, group strategy, leakage risks, limitations, checksum policy

Output:
- `docs/methodology/datasets/OP_SPAM_CARD.md`
- `docs/methodology/datasets/MU3D_CARD.md`
- `docs/methodology/datasets/RLT_CARD.md`

Done criterion:
- every dataset has a card
- every card has required fields
- unavailable datasets are explicitly blocked, not silently passed

Gate:
- `DATASET_CARDS_COMPLETE`

## B3. Dataset audit artifact

Input:
- dataset cards
- dataset manifests

Transform:
- validate completeness and consistency

Output:
- `artifacts/verification/DATASET_CARDS_AUDIT.json`

Done criterion:
- 100% required fields present
- no card contradicts manifest

Gate:
- `DATASET_CARDS_AUDIT_PASS`

---

# Track C — Metric and Calibration Gates

## C1. Reliability diagram shape validator

Input:
- `PHASE0_RELIABILITY_DIAGRAM.json`

Transform:
- validate bin count, monotonic edges, count sums, dataset names

Output:
- validator result

Done criterion:
- 10 bins
- monotonic bin edges
- count sum equals reported sample count where available

Gate:
- `RELIABILITY_SHAPE_PASS`

## C2. Phase 0 metric completeness validator

Input:
- `PHASE0_VERIFIABILITY.json`

Transform:
- assert that every computed dataset has AUC, CI, ECE before/after, Brier before/after

Output:
- validator result

Done criterion:
- no computed dataset has null metric
- unavailable dataset is explicitly marked unavailable

Gate:
- `PHASE0_METRIC_COMPLETENESS_PASS`

## C3. Phase unlock consistency validator

Input:
- Phase 0 artifact
- configured AUC threshold

Transform:
- verify `phase1_unlocked` matches dataset results

Output:
- validator result

Done criterion:
- Phase 1 unlock cannot contradict metric artifact

Gate:
- `PHASE_UNLOCK_CONSISTENCY_PASS`

## C4. Probability emission policy validator

Input:
- output contract
- calibration artifact
- API/UI output fixtures

Transform:
- assert probability appears only when allowed by calibration policy

Output:
- validator result

Done criterion:
- no unsupported probability leaves system boundary

Gate:
- `PROBABILITY_POLICY_PASS`

---

# Track D — Domain Distance Policy

## D1. Domain taxonomy

Input:
- empirical validation results
- dataset cards

Transform:
- classify every dataset pair as in-domain, adjacent-domain, or out-of-domain

Output:
- `docs/methodology/DOMAIN_DISTANCE_POLICY.md`

Done criterion:
- every reported metric has a domain regime

Gate:
- `DOMAIN_TAXONOMY_PASS`

## D2. Domain-distance artifact

Input:
- domain policy
- metric artifacts

Transform:
- emit machine-readable domain policy

Output:
- `artifacts/verification/DOMAIN_DISTANCE_POLICY.json`

Done criterion:
- every probability policy references domain distance

Gate:
- `DOMAIN_DISTANCE_POLICY_PASS`

## D3. Cross-domain output restriction

Input:
- API output fixtures
- domain policy artifact

Transform:
- enforce ordinal-only output for uncalibrated or out-of-domain regimes

Output:
- test result

Done criterion:
- uncalibrated cross-domain output has no float probability

Gate:
- `CROSS_DOMAIN_ORDINAL_ONLY_PASS`

---

# Track E — Methodology Consistency

## E1. Methodology surface inventory

Input:
- README
- docs
- API methodology endpoint
- UI text
- artifacts

Transform:
- enumerate every product-boundary statement

Output:
- `artifacts/verification/METHODOLOGY_SURFACE_INDEX.json`

Done criterion:
- every surface is listed

Gate:
- `METHODOLOGY_SURFACE_INDEX_PASS`

## E2. Methodology consistency validator

Input:
- surface index
- methodology docs
- artifacts

Transform:
- compare thresholds, claims, commands, artifact paths, policy language

Output:
- `artifacts/verification/METHODOLOGY_CONSISTENCY.json`

Done criterion:
- no contradiction between README, docs, API, UI, and artifacts

Gate:
- `METHODOLOGY_CONSISTENCY_PASS`

---

# Track F — UI Epistemic Clarity

## F1. Result card limitation state

Input:
- UI result card
- API response fixture

Transform:
- render limitation state near output

Output:
- UI fixture / screenshot-independent DOM assertion

Done criterion:
- every result card shows whether output is calibrated, ordinal-only, or insufficient

Gate:
- `UI_LIMITATION_STATE_PASS`

## F2. Missing evidence display

Input:
- evidence graph
- missing evidence list

Transform:
- render missing evidence and next verification question

Output:
- UI DOM state

Done criterion:
- every result has at least one next corroboration question or explicit insufficient-data state

Gate:
- `UI_MISSING_EVIDENCE_PASS`

## F3. UI clarity artifact

Input:
- UI tests
- fixture results

Transform:
- emit clarity audit artifact

Output:
- `artifacts/verification/UI_EPISTEMIC_CLARITY.json`

Done criterion:
- no result card lacks limitation state

Gate:
- `UI_EPISTEMIC_CLARITY_PASS`

---

# Track G — Release Claim Audit

## G1. Product claim scanner

Input:
- README
- docs
- UI source
- API strings
- package metadata

Transform:
- scan for unsupported product claims and forbidden person-level framing

Output:
- scanner result

Done criterion:
- unsupported claims fail closed

Gate:
- `RELEASE_CLAIM_SCAN_PASS`

## G2. Release claim audit artifact

Input:
- product claim scanner result

Transform:
- write audit artifact

Output:
- `artifacts/verification/RELEASE_CLAIM_AUDIT.json`

Done criterion:
- release cannot pass without the artifact

Gate:
- `RELEASE_CLAIM_AUDIT_PASS`

---

# Final Execution DAG

```text
A1 -> A2 -> A3 -> A4
B1 -> B2 -> B3
C1 -> C2 -> C3 -> C4
D1 -> D2 -> D3
E1 -> E2
F1 -> F2 -> F3
G1 -> G2
```

Integration order:

```text
Claim precision
-> Data provenance
-> Metric hardening
-> Domain policy
-> Methodology consistency
-> UI clarity
-> Release claim audit
```

Final gate:

```text
make cogveritas-verify
make verify-release
```

Completion state:

```text
COGVERITAS_VERIFY_COMPLETE
VERIFY_RELEASE_PASS
```
