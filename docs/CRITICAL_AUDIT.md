# Critical Audit v0.4.0

## What was weak before v0.4.0

1. Scoring was too simple.
2. There was no explicit anti-pseudoscience guard.
3. There was no red-team loop.
4. There was no entropy simulation.
5. Evidence graph structure existed only implicitly.

## What v0.4.0 improves

- Conservative calibration with reliability weights.
- Single-modality confidence cap.
- Counter-evidence damping.
- Evidence graph entropy metric.
- Red-team cases.
- Simulation command.
- Report quality gate.
- New tests around calibration, pseudoscience and red-team behavior.

## What is still not solved

- Real video/audio feature extraction remains adapter-level, not full production inference.
- Dataset benchmarking is not yet wired to external corpora.
- No multilingual semantic entailment model is integrated.
- No diarization/audio/vision runtime container is included.
- No human annotation UI yet.

## Next PR

Implement `media_pipeline_v1`:

1. video/audio ingestion;
2. Whisper transcript adapter runtime;
3. openSMILE acoustic feature import;
4. OpenFace/MediaPipe feature import;
5. multimodal evidence normalization;
6. benchmark dataset loader;
7. calibration report with false-positive target.
