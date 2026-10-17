# COGVERITAS Elite Quality Protocol

Status: operational protocol.
Mode: fail-closed.
Purpose: raise COGVERITAS from working research-product code to elite verification quality.

## 1. Direction

The next level is not more model surface. The next level is stronger evidence discipline.

COGVERITAS must optimize for:

1. external checkability,
2. provenance completeness,
3. calibration honesty,
4. cross-domain stability,
5. bias resistance,
6. reproducible artifacts,
7. human-review utility,
8. no person-level verdict.

## 2. Recursive Quality Law

Apply the same gate at every scale:

```text
unit -> claim -> document -> dataset -> metric -> API -> UI -> release
```

Each layer must answer:

```text
What is the evidence?
What is missing?
What is calibrated?
What fails closed?
What must a human verify next?
```

If a layer cannot answer, it is not elite-ready.

## 3. Current Verified State

The repository already has:

- COGVERITAS public boundary in README,
- Phase 0 gates in Makefile,
- no-verdict output contract,
- verifiability tagger,
- grouped CV runner,
- calibration metrics,
- fail-closed artifact gates,
- machine-readable methodology endpoint,
- empirical validation showing strong limits outside narrow domains.

This is a valid foundation. The next work is quality hardening, not conceptual expansion.

## 4. Main Quality Gaps

### Gap A — Claim segmentation precision

Current sentence-level claim extraction is stable but too coarse. Elite level requires NP+VP claim slicing with deterministic fallback.

Required upgrade:

- split compound sentences into atomic claims,
- preserve original sentence provenance,
- assign stable claim ids,
- never lose the original text span,
- test clause-level edge cases.

### Gap B — Dataset provenance depth

Dataset manifests exist, but elite level requires dataset cards.

Required upgrade:

- source URL,
- access date,
- license notes,
- schema,
- grouping strategy,
- limitations,
- known leakage risks,
- split strategy,
- checksum policy,
- raw-data non-commit policy.

### Gap C — Gate completeness

`make cogveritas-verify` must prove the full chain, not only artifact presence.

Required upgrade:

- include phase0-metrics in verify order,
- run mypy with explicit target,
- fail if reliability bins are malformed,
- fail if any computed dataset lacks CI,
- fail if phase1_unlocked contradicts dataset results,
- fail if methodology endpoint disagrees with artifacts.

### Gap D — Cross-domain honesty

Elite quality requires explicit domain-distance policy.

Required upgrade:

- classify every dataset result as in-domain, adjacent-domain, or out-of-domain,
- emit probability only for calibrated in-domain regimes,
- emit ordinal-only review flags outside validated regimes,
- add domain-distance field to metric artifacts.

### Gap E — UI epistemic clarity

UI must show why an output is limited.

Required upgrade:

- show no-verdict rationale near every result,
- show calibration state,
- show missing evidence,
- show corroboration questions,
- never show a score without its allowed-use state.

## 5. Elite Gate Set

Add these gates after the current Phase 0 gates:

```yaml
gates:
  - name: atomic_claim_quality
  - name: dataset_card_completeness
  - name: reliability_shape
  - name: domain_distance_policy
  - name: methodology_artifact_consistency
  - name: ui_epistemic_clarity
  - name: release_claim_audit
```

## 6. Required New Artifacts

```text
artifacts/verification/CLAIM_SEGMENTATION_QUALITY.json
artifacts/verification/DATASET_CARDS_AUDIT.json
artifacts/verification/DOMAIN_DISTANCE_POLICY.json
artifacts/verification/METHODOLOGY_CONSISTENCY.json
artifacts/verification/UI_EPISTEMIC_CLARITY.json
artifacts/verification/RELEASE_CLAIM_AUDIT.json
```

## 7. Acceptance Thresholds

```text
atomic_claim_quality:
  95% deterministic span preservation on fixture set

dataset_card_completeness:
  100% required fields present for every dataset

reliability_shape:
  10 bins, monotonic bin edges, count sum equals n_samples

domain_distance_policy:
  no probability emitted outside validated/calibrated regime

methodology_artifact_consistency:
  README, API methodology endpoint, docs, and artifacts agree

ui_epistemic_clarity:
  every result card shows limitation + next verification question

release_claim_audit:
  no unsupported product claim in README, docs, UI, API, or package metadata
```

## 8. PR Sequence

### PR 1 — Atomic claim segmentation

Scope:

- improve claim segmentation beyond one sentence = one claim,
- add span offsets,
- add fixture tests,
- preserve deterministic fallback.

Acceptance:

- existing tests pass,
- new claim segmentation quality artifact emitted,
- no output contract change.

### PR 2 — Dataset cards and domain-distance policy

Scope:

- add dataset cards,
- add domain-distance artifact,
- define in-domain vs out-of-domain probability policy.

Acceptance:

- missing field fails closed,
- probability policy enforced by gate.

### PR 3 — Gate hardening

Scope:

- harden `scripts/cogveritas_gates.py`,
- include phase0-metrics in verify order,
- run mypy with explicit target,
- validate reliability diagram shape,
- validate methodology consistency.

Acceptance:

- `make cogveritas-verify` proves full chain.

### PR 4 — UI epistemic clarity

Scope:

- show limitation state,
- show calibration state,
- show missing evidence,
- show corroboration questions.

Acceptance:

- no result card lacks its allowed-use state.

### PR 5 — Release claim audit

Scope:

- scan README/docs/UI/API/package metadata for unsupported claims,
- block release on overclaiming.

Acceptance:

- unsupported product claims fail closed.

## 9. Final Elite Command

```bash
make cogveritas-verify
make verify-release
```

Required terminal state:

```text
COGVERITAS_VERIFY_COMPLETE
VERIFY_RELEASE_PASS
```

## 10. Elite Definition

Elite quality is reached when the system is more trustworthy because it refuses to overclaim.

The winning property is not a larger number.
The winning property is a calibrated boundary that survives contact with external data.
