# COGVERITAS Phase 0 Execution Scaffold

Status: fail-closed execution scaffold.

Repository base: neuron7xLab/bive.

Goal: add a Phase 0 verbal verifiability gate that extracts externally checkable claims, preserves provenance, emits calibration artifacts, and keeps the no-verdict invariant.

## Required scope

- dataset manifests
- verifiability tagger
- grouped cross-validation runner
- calibration metrics
- reliability diagram data
- baseline comparison gate
- no-verdict output contract
- CI gate stubs
- methodology documentation

## Required files

- src/cogveritas/verifiability_tagger.py
- src/cogveritas/phase0_cv.py
- src/cogveritas/calibration_metrics.py
- src/cogveritas/bias_baseline.py
- src/cogveritas/output_contract.py
- scripts/run_phase0_verifiability.py
- artifacts/datasets/mu3d_manifest.json
- artifacts/datasets/op_spam_manifest.json
- artifacts/verification/PHASE0_VERIFIABILITY.json
- artifacts/verification/PHASE0_RELIABILITY_DIAGRAM.json
- artifacts/verification/PHASE0_BIAS_BASELINE.json

## Hard gates

- missing artifact fails closed
- unsupported probability output is disabled
- later phases remain blocked until Phase 0 metrics pass
- release remains blocked if baseline comparison fails
- verdict remains None

## Final command

```bash
make cogveritas-verify
```

Expected terminal markers:

```text
UNIT_TESTS_PASS
RUFF_PASS
MYPY_STRICT_PASS
PHASE0_VERIFIABILITY_ARTIFACT_PRESENT
SUBJECT_INDEPENDENT_AUC_GATE_PASS_OR_PHASE1_BLOCKED
CALIBRATION_ECE_GATE_PASS_OR_FLOATS_DISABLED
BIAS_BASELINE_GATE_PASS_OR_RELEASE_BLOCKED
NO_VERDICT_INVARIANT_PASS
ARTIFACT_MANIFEST_PASS
COGVERITAS_VERIFY_COMPLETE
```
