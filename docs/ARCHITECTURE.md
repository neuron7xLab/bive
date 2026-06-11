# Architecture

BIVE is an evidence-first verification system.

```text
Media/Text Input
  -> Ingest Layer
  -> Claims Layer
  -> Signal Extraction Layer
     -> text
     -> audio adapter
     -> vision adapter
     -> context adapter
  -> EvidenceEvent Ledger
  -> Evidence Fusion Engine
  -> Falsifier
  -> Red-Team Review
  -> VerificationReport
  -> PR / CI / Reproducibility Gate
```

## Core architectural invariants

1. No module may output a person-level accusation.
2. Every signal must be represented as an `EvidenceEvent` with confidence, magnitude, direction, limitations, and provenance.
3. Multimodal features are not truth. They are review surfaces.
4. Elevated risk must include alternative explanations.
5. Absence of evidence must increase uncertainty, not confidence.
6. The system must fail closed when adapters or evidence are missing.

## Domain layers

- **Linguistic layer:** claims, hedging, absolutes, temporal anchors, contradiction candidates, pressure-to-trust patterns.
- **Paralinguistic layer:** optional acoustic features from openSMILE / Whisper / diarization pipelines.
- **Kinesic/vision layer:** optional OpenFace / MediaPipe / MMPose-style features.
- **Context layer:** timelines, external documents, OSINT records, contradiction graph.
- **Falsification layer:** alternatives, missing evidence, disconfirming questions.

## Why adapters are optional

The deterministic package must run without GPU, cameras, secret tokens, or heavyweight research tools. Production multimedia extraction belongs behind adapters. Core validity belongs in schemas, scoring, falsification, provenance, and test gates.
