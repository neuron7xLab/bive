# Product Operating Model

BIVE is packaged as an evidence-first engineering product candidate, not as a deployed production service.

## Product category

Evidence-first behavioral intelligence and automation-of-automation research platform.

## Primary user

Independent AI systems architect, research engineer, security-conscious automation builder, technical reviewer, or product engineer who needs bounded evidence artifacts instead of unverifiable behavioral conclusions.

## Core product job

Convert ambiguous transcript or automation intent into a bounded artifact:

- evidence graph;
- hypotheses with uncertainty;
- missing evidence;
- human-review questions;
- runtime contracts;
- release gates;
- AOS intent/execution contracts.

## Hard non-claims

BIVE is not:

- a lie detector;
- a diagnosis engine;
- a guilt engine;
- an automated intent detector;
- a deployed production SaaS;
- a substitute for legal, clinical, employment, security, or human-subject review.

## Product manager contract

A feature is accepted only if it changes at least one execution path:

1. improves evidence visibility;
2. reduces false certainty;
3. strengthens security or privacy boundary;
4. makes readiness more observable;
5. adds a binary gate;
6. improves package/install/release reproducibility;
7. makes a customer-facing workflow more direct without hiding risk.

Decorative concepts are rejected unless they compile into mechanism, schema, validator, test, or release gate. Humanity may continue inventing slogans elsewhere; this repository does not need more of them.

## Release claim boundary

Allowed public claim:

> Open-source engineering product candidate with local verification evidence, API/UI/CLI shell, AOS prompt OS, neurocognitive-control analogies mapped to validators, and explicit production unknowns.

Forbidden public claim:

> Production deployed behavioral decision system.

## Runtime artifact

Machine-readable model:

- `data/product/product_operating_model.json`
- `data/product/industrial_release_scorecard.json`
- `src/bive/resources/product_operating_model.json`
- `src/bive/resources/industrial_release_scorecard.json`

Runtime access:

- CLI: `bive-aos product`
- API: `GET /api/v1/system/product-readiness?api-version=2026-06-11`
- Gate: `make product-readiness`

## Acceptance

Product-readiness status must remain non-GREEN while any external release-critical gates are `UNKNOWN` or `HUMAN_REVIEW_REQUIRED`.
