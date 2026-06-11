# BIVE Product Specification

## Product definition

BIVE is an evidence-first transcript verification engine with a CLI, FastAPI backend, SQLite persistence and static operational frontend. It converts transcript segments into structured evidence events, calibrated hypotheses, missing-evidence notes and verification questions.

## Users

- analysts and auditors;
- investigative researchers;
- journalists and OSINT teams;
- safety and governance reviewers;
- engineers validating evidence pipelines.

## Supported workflow

1. Provide transcript JSON.
2. Validate schema and runtime limits.
3. Build evidence graph and report.
4. Store report locally.
5. Inspect report through UI/API/CLI.
6. Export JSON or Markdown for human review.

## Capability state

- Text transcript analysis: implemented and release-gated.
- Evidence graph and report model: implemented and release-gated.
- CLI: implemented and release-gated.
- API: implemented and release-gated.
- Static frontend: implemented and frontend-quality gated.
- SQLite report storage: implemented with readiness healthcheck and stats.
- Dependency CVE audit: implemented as command, externally gated by network availability.
- Docker runtime verification: implemented as command, externally gated by Docker availability.
- Audio/video adapters: optional extension points, not required for core release.

## Safety boundary

BIVE never produces automatic person-level lie, guilt, truthfulness or legal verdicts. It produces reviewable evidence and questions for external corroboration.
