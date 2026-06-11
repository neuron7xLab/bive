# Cognitive Control Plane

BIVE Stage 10 adds a deterministic cognitive-control layer for AOS execution.

The layer is not a claim of biological intelligence. It is an engineering control model:

- excitation increases when intent clarity, evidence strength, reversibility, dependency readiness and failure visibility increase;
- inhibition increases when risk, uncertainty, irreversibility, complexity and human-gate pressure increase;
- bounded execution is allowed only when excitation is strong enough and inhibition remains within the safe range;
- HIGH and CRITICAL requests route to human review even when the request looks operationally clear;
- GREEN remains impossible without executed evidence.

## Runtime artifacts

- `src/bive/cognitive_control.py`
- `data/aos/cognitive_control_plane.json`
- `src/bive/resources/cognitive_control_plane.json`
- `scripts/validate_cognitive_control_plane.py`
- `tests/test_cognitive_control_plane.py`
- `make cognitive-control`
- API: `/api/v1/system/cognitive-control-plane?api-version=2026-06-11`

## Agent roles

1. `intent_compiler`: extracts executable intent.
2. `boundary_detector`: detects risk and human-gated actions.
3. `contract_engineer`: checks contract readiness.
4. `verification_engineer`: blocks unsupported GREEN.
5. `critical_auditor`: checks failure visibility.
6. `repair_optimizer`: selects the smallest reversible closure step.

## Balance rule

The system does not maximize action. It maximizes controlled closure:

```text
controlled_closure = excitation + evidence + failure_visibility - inhibition
```

This prevents the common automation failure where a system becomes faster while becoming less verifiable. Humanity keeps reinventing that trap and naming it velocity.
