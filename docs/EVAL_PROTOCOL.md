# Evaluation Protocol

## Mandatory metrics

- Accuracy only as a weak headline metric.
- Precision and recall.
- False positive rate.
- False negative rate.
- Calibration error.
- Cross-dataset generalization.
- Ablation by modality.
- Robustness under noise, compression, low light, and transcript error.
- Human-review usefulness score.

## Forbidden evaluation pattern

Do not optimize only for benchmark score. A false positive accusation is high harm. The system must prefer uncertainty over unsupported confidence.

## Baseline ladder

1. Text-only lexical baseline.
2. Text + claim contradiction graph.
3. Audio-only acoustic stress baseline.
4. Vision-only action-unit/pose baseline.
5. Multimodal fusion.
6. Multimodal + context graph.
7. Multimodal + falsifier + red-team.

## Acceptance threshold for real data experiments

A model cannot be promoted unless it passes:

- held-out dataset split;
- domain-shift split;
- false-positive audit;
- calibration audit;
- explainability audit;
- missing-evidence behavior audit.
