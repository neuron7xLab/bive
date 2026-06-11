# Calibration Model v0.4.0

BIVE converts evidence events into hypotheses through a conservative logit update.

## Why this exists

The system must fight two failures:

1. under-reaction: ignoring meaningful contradictions;
2. over-reaction: turning weak cues into accusations.

The second failure is more dangerous because it creates pseudo-authority. So v0.4.0 applies penalties for single-modality evidence, missing context and unresolved counter-evidence.

## Deterministic weights

Weights live in `src/bive/weights.py`.

- text reliability: 0.82
- context reliability: 0.90
- audio reliability: 0.62
- vision reliability: 0.58
- system reliability: 0.75
- single-modality penalty: 0.18
- high-confidence cap without multimodal support: 0.66

## Interpretation

A high score means: “review this hypothesis with more evidence.”
It never means: “the person is guilty” or “the person is lying.”

## Failure handling

If uncertainty is high, final status remains `inconclusive` or `review_required`. BIVE prefers honest incompleteness over theatrical certainty, because civilization already has enough people pretending spreadsheets are reality.
