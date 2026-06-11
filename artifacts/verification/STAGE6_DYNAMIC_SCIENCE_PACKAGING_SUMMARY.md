# Stage 6 Dynamic Science Packaging Evidence

## Machine additions

- `src/bive/science.py`
- `src/bive/resources/science_registry.json`
- `data/science/science_registry.json`
- `data/operations/dynamic_scenarios.json`
- `scripts/validate_science_registry.py`
- `scripts/dynamic_environment_probe.py`
- `tests/test_science_registry.py`
- `tests/test_science_api_contract.py`
- `tests/test_dynamic_environment_probe.py`

## Gates added

- `make science-registry`
- `make dynamic-probe`

## Runtime endpoints added

- `/api/v1/system/science-registry`
- `/api/v1/system/science-registry/full`

## Boundary

The registry is intentionally bounded: it prevents the repository from converting behavioral science, psychophysiology, cognitive science, affective computing, or linguistic signals into automatic person-level lie/guilt/intent/diagnosis verdicts.
