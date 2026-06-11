# Open Source Stack

## Core runtime

- Python 3.10+
- stdlib-only deterministic core
- pytest, ruff, mypy for PR gates
- JSON Schema for public data contracts

## Optional multimedia adapters

- Whisper / faster-whisper / WhisperX for ASR and timestamps.
- pyannote.audio for speaker diarization.
- openSMILE for acoustic features.
- OpenFace / LibreFace for landmarks, head pose, gaze, Action Units.
- MediaPipe / MMPose for pose, face, and hand landmarks.

## MLOps and reproducibility

- DVC for dataset/model versioning.
- MLflow for experiment tracking and model registry.
- Evidently for evaluation and monitoring.
- W3C PROV-compatible provenance export.

## Rule

No optional tool may be a hidden dependency of the deterministic core. If a tool is absent, the adapter returns `ok=false` and the report uncertainty increases.
