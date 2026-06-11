# Simulation Protocol v0.4.0

BIVE includes deterministic scenario simulation for entropy resistance.

## Scenarios

- `calm_verified`: cooperative verification language.
- `pressure_no_check`: discourages verification.
- `temporal_contradiction`: local contradiction across time.
- `high_entropy_noise`: hedging and uncertainty with explicit permission to verify.

## Command

```bash
python -m bive.cli simulate
```

## Design target

The system must remain calm when evidence is weak and become review-oriented when contradiction or anti-verification pressure appears.

## Meaning

Simulation is not scientific validation. It is an engineering immune system. Real validation requires datasets, baselines, ablations and external review.
