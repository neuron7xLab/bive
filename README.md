# BIVE v0.4.0 — Behavioral Integrity Verification Engine

[![CI](https://github.com/neuron7xLab/bive/actions/workflows/ci.yml/badge.svg)](https://github.com/neuron7xLab/bive/actions/workflows/ci.yml)
[![CodeQL](https://github.com/neuron7xLab/bive/actions/workflows/codeql.yml/badge.svg)](https://github.com/neuron7xLab/bive/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/neuron7xLab/bive/badge)](https://scorecard.dev/viewer/?uri=github.com/neuron7xLab/bive)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)

BIVE is an evidence-first transcript verification system. It builds reviewable evidence graphs, calibrated hypotheses, counter-evidence, uncertainty, missing-evidence lists and follow-up questions. It does **not** label people as liars, guilty or truthful.

## Product boundary

BIVE is a research-to-product engineering repository for analysts, auditors, investigators, journalists, OSINT teams and safety researchers who need structured evidence review. It is not an automated decision system. Any real-world decision that affects a person requires human review, domain expertise and external corroboration.

## Current executable scope

- deterministic transcript ingestion;
- conservative text-feature and claim extraction;
- local contradiction/tension detection;
- evidence event model with provenance;
- calibrated hypothesis fusion with reliability weights;
- evidence graph entropy signal;
- anti-pseudoscience quality gate;
- built-in red-team and simulation gates;
- FastAPI backend, SQLite storage and packaged static web UI;
- operational API: health, liveness, readiness, metrics, system status, design contract, interface contract and science registry;
- frontend console: demo payload, API token flow, report summary, evidence cards, hypotheses, human-review questions, raw JSON and Markdown export;
- safe frontend rendering: no raw dynamic HTML injection for transcript/report-derived data;
- wheel smoke, API smoke, schema, metadata, frontend-quality, science-registry, dynamic-probe, OpenAPI and release-manifest gates;
- GitHub CI, PR template, issue templates, security policy and release checklist;
- AOS Prompt OS layer: prompt kernel, eval harness, scoring schema, execution contracts, CLI, API endpoint and validation gate;
- product operating layer: product model, jobs-to-be-done, activation path, industrial release scorecard, explicit GitHub-vs-production decision boundary.

## Install and verify

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,api,security]"
python -m pip check
python scripts/check_environment.py
make verify-release
```

Expected terminal invariants:

```text
[BIVE PREFLIGHT] pass
VERIFY_RELEASE_PASS
```

The repository uses an in-tree PEP 517/660 backend, so editable installs do not need to download setuptools before project metadata can be read. If a package index or proxy is unavailable, dependency installation can still fail; use a pre-populated wheel cache or the pinned `constraints/py310.txt` / `requirements/*.txt` files and rerun the same commands. `make bootstrap-env` remains a convenience wrapper around the constrained local setup path.

## CLI

```bash
bive analyze --input samples/demo_transcript.json --output artifacts/local_demo_report.json
bive validate --input artifacts/local_demo_report.json
bive render --input artifacts/local_demo_report.json --output artifacts/local_demo_report.md
bive simulate
bive red-team
bive gate --input artifacts/local_demo_report.json
bive-aos status
bive-aos compile "Automate a repository release with evidence gates"
bive-aos neurocognitive
bive-aos product
```

## API and UI

Local development:

```bash
make api
# open http://127.0.0.1:8080
```

Production/staging requires an API token:

```bash
export BIVE_ENV=production
export BIVE_API_TOKEN='replace-with-real-secret'
bive-api
```

Core endpoints:

- `GET /health`
- `GET /livez`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/capabilities`
- `GET /api/v1/system/status`
- `GET /api/v1/system/design-contract`
- `GET /api/v1/system/interface-contract`
- `GET /api/v1/system/science-registry`
- `GET /api/v1/system/science-registry/full`
- `GET /api/v1/system/aos-kernel`
- `GET /api/v1/system/cognitive-control-plane`
- `GET /api/v1/system/neurocognitive-protocol`
- `GET /api/v1/system/product-readiness`
- `POST /api/v1/reports/from-transcript`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `GET /api/v1/reports/{report_id}/markdown`

OpenAPI contract: `docs/openapi.json`.

## Release gates

```bash
make repo-clean
make metadata
make lint
make typecheck
make test
make coverage
make schema
make ui-check
make frontend-quality
make science-registry
make aos-kernel
make cognitive-control
make neurocognitive-protocol
make product-readiness
make dynamic-probe
make openapi
make api-smoke
make wheel-smoke
make security-static
make manifest-check
```

Dependency CVE state and Docker runtime verification require network/Docker availability:

```bash
make dependency-audit
make docker-build
```

## Repository map

- `src/bive/` — core package, CLI, API, storage, report model;
- `src/bive/web/` — static operational frontend shipped inside the wheel;
- `schemas/` — JSON contracts;
- `prompts/`, `evals/`, `contracts/`, `data/aos/` — AOS prompt OS, eval tasks, scoring schema and automation contract templates;
- `tests/` — executable behavior and contract tests;
- `scripts/` — release, schema, metadata, OpenAPI, frontend, science-registry, dynamic-probe and manifest tools;
- `data/science/` — mirrored bounded science registry for repository review;
- `data/operations/` — dynamic environment scenario registry;
- `docs/` — architecture, operations, security, dynamic environment, science registry, release gates, design system and research protocols;
- `.github/` — CI, PR and issue workflow.

## Non-negotiable invariant

BIVE outputs evidence for review. It must not output automatic person-level verdicts, guilt claims, deterministic lie labels or decisions that bypass human review.

## Stage 8 Microsoft hardening

The API now requires `api-version=2026-06-11` on `/api/v1/*`, emits Microsoft-style error envelopes, propagates `x-ms-request-id`, echoes `x-ms-client-request-id`, validates a STRIDE threat model, and ships compiled dependency intent files.


## Stage 10 Cognitive Control Plane

BIVE now includes an AOS cognitive-control layer that computes excitation/inhibition weights, multi-agent votes, fractal invariant checks and reverse-inference remediation plans.

Run:

```bash
make cognitive-control
bive-aos control "Inspect repository and produce reversible verification tasks"
```

API:

```text
GET /api/v1/system/cognitive-control-plane?api-version=2026-06-11
```

The layer does not claim biological intelligence. It is a deterministic governance mechanism for balancing action pressure against risk, uncertainty, complexity and missing evidence.

## Stage 10: cognitive control and neurocognitive operational protocol

Stage 10 adds a bounded cognitive-control layer for AOS execution. It is not a biological-brain claim. It maps CNS-inspired functions to executable repository mechanisms:

- excitation/inhibition balance -> `src/bive/cognitive_control.py`;
- salience gating -> risk/evidence/failure routing;
- working-memory budget -> AOS intent contract and context capsule discipline;
- error monitoring -> adversarial verifier and release gates;
- predictive reverse inference -> missing-evidence closure plan;
- homeostatic stability -> safe weight ranges;
- fractal invariant recursion -> repeated checks across intent, boundary, contract, verification and release;
- plasticity calibration -> prompt/kernel changes only from measured eval failure.

Runtime inspection:

```bash
make cognitive-control
make neurocognitive-protocol
bive-aos neurocognitive
bive-cognitive-control "Inspect repository and produce bounded verification tasks"
```

## Product readiness state

Current packaged state is an open-source GitHub product candidate, not a deployed production service. `make product-readiness` and `/api/v1/system/product-readiness?api-version=2026-06-11` intentionally keep the product at non-GREEN while dependency CVE audit, Docker runtime, deployment smoke and human-impact review remain external gates.
