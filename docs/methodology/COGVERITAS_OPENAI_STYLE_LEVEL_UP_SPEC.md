# COGVERITAS Institutional Level-Up Specification

Version: 1.0
Status: Draft for execution
Owner: neuron7xLab
Repository: neuron7xLab/bive
Mode: fail-closed
Language: normative English

## 1. Purpose

This specification defines the requirements for raising COGVERITAS from a strong internal research-product prototype to an institution-grade verification system.

The document intentionally follows a formal safety-and-evaluation structure: scope, boundary, capability claims, evaluation gates, risk controls, artifacts, release criteria, escalation rules, and change control.

COGVERITAS MUST NOT be assessed by velocity, number of pull requests, narrative coherence, or green CI alone. It MUST be assessed by independently reproducible evidence, calibrated limitations, external-fact anchoring, and enforced release gates.

## 2. External Reference Model

The level-up program is aligned to the following external evaluation patterns:

1. Risk governance and measurement discipline.
   - The system MUST separate governance, measurement, release management, and post-release monitoring.

2. Preparedness-style capability assessment.
   - The system MUST define tracked capabilities, thresholds, safeguards, review ownership, and stop conditions.

3. Frontier-safety-style early-warning evaluation.
   - The system MUST identify capability levels, define evaluations that detect threshold crossing, and apply mitigation before product claims expand.

4. Repository-agent benchmark discipline.
   - The system MUST control contamination, stale benchmark reuse, hidden leakage, and non-reproducible evaluation results.

5. Resource-effectiveness accounting.
   - The system MUST report not only whether a gate passes, but also the cost, time, compute, and failure mode of reaching that result.

## 3. Current Maturity Classification

The current state is classified as:

```text
Maturity Band: 6.5-7.0 / 10
Class: strong internal research-product prototype
Not yet: institution-grade
Not yet: externally replicated benchmark-grade system
```

### 3.1 Corrected scorecard

```text
Architecture discipline:        7.0 / 10
Risk governance:                6.5 / 10
Metric validity:                6.0 / 10
Cross-domain evidence:          5.5 / 10
CI and release discipline:      7.5 / 10
Product workflow:               7.0 / 10
Overclaim control:              7.5 / 10
Data reproducibility maturity:  5.5 / 10
Overall:                        6.6 / 10
```

The score MUST NOT be raised above 7.0 unless benchmark-card, contamination-audit, domain-distance, and replication gates exist as executable artifacts.

The score MUST NOT be raised above 8.0 unless the evaluation package can be reproduced from a fresh environment.

The score MUST NOT be raised above 9.0 unless an independent replication package, resource-effectiveness report, threat model, and release-claim audit are enforced in CI.

## 4. Product Boundary

COGVERITAS is an evidence-review and external-checkability system.

It MUST:

- extract externally checkable claims;
- preserve provenance;
- expose missing evidence;
- generate corroboration questions;
- route claims to external record types;
- surface timelines and inconsistency candidates for human review;
- emit structured limitations;
- block unsupported probabilities;
- keep verdict equal to null.

It MUST NOT:

- determine person-level truth status;
- present itself as an automatic adjudication system;
- emit probability-like values without calibration evidence;
- treat internal linguistic coherence as evidence;
- treat green CI as product validity;
- claim cross-domain reliability without cross-domain artifacts.

## 5. Capability Registry

The system SHALL maintain a machine-readable capability registry.

Each capability MUST define:

```yaml
capability_id: string
name: string
intended_use: string
non_goals: string[]
inputs: string[]
outputs: string[]
known_failure_modes: string[]
required_artifacts: string[]
release_gate: string
owner: string
status: proposed | experimental | validated_internal | externally_replicated | deprecated
```

Initial tracked capabilities:

```text
CV-C1: External-checkability claim extraction
CV-C2: Corroboration worklist routing
CV-C3: Timeline construction
CV-C4: Inconsistency candidate detection
CV-C5: Analyst dossier export
CV-C6: Interview question generation for missing checkable detail
CV-C7: Dataset and domain-distance policy
CV-C8: Release-claim audit
```

No capability may be called production-ready unless its required artifacts exist and its release gate passes.

## 6. Evaluation Doctrine

### 6.1 Evaluation levels

The system MUST support four evaluation levels:

```text
L0: unit correctness
L1: contract invariants
L2: dataset-level metrics
L3: cross-domain robustness
L4: independent reproduction
```

A release is institution-grade only if L0-L3 pass.
A release is benchmark-grade only if L0-L4 pass.

### 6.2 Required metric package

Every quantitative claim MUST include:

```yaml
dataset: string
source: string
access_date: string | null
split_strategy: string
group_key: string | null
n_samples: integer
n_groups: integer | null
metric_name: string
metric_value: number
confidence_interval: [number, number] | null
calibration_metric: string | null
leakage_notes: string
known_limitations: string
artifact_sha256: string
```

A metric without dataset, split strategy, confidence interval policy, and limitation text MUST be treated as invalid.

## 7. Mandatory Artifacts

The following artifacts MUST exist before the maturity score can exceed 7.0:

```text
artifacts/verification/BENCHMARK_CARD.json
artifacts/verification/CONTAMINATION_AUDIT.json
artifacts/verification/CROSS_DOMAIN_MATRIX.json
artifacts/verification/DOMAIN_DISTANCE_POLICY.json
artifacts/verification/PRODUCT_CLAIM_AUDIT.json
artifacts/verification/RESOURCE_EFFECTIVENESS.json
artifacts/verification/EXTERNAL_REPLICATION_READINESS.json
```

The following documents MUST exist:

```text
docs/methodology/BENCHMARK_CARD.md
docs/methodology/CONTAMINATION_AUDIT.md
docs/methodology/DOMAIN_DISTANCE_POLICY.md
docs/methodology/RESOURCE_EFFECTIVENESS.md
docs/methodology/PRODUCT_CLAIM_POLICY.md
docs/methodology/EXTERNAL_REPLICATION_GUIDE.md
docs/security/MISUSE_THREAT_MODEL.md
```

## 8. Benchmark Card Requirement

A benchmark card MUST describe each evaluation suite.

Minimum fields:

```yaml
benchmark_name: string
benchmark_version: string
task_type: string
data_source: string
license_notes: string
collection_date: string | null
contamination_risk: low | medium | high | unknown
split_strategy: string
grouping_strategy: string | null
leakage_controls: string[]
metrics: string[]
calibration_policy: string
known_limitations: string[]
reproducibility_command: string
```

Release gate:

```text
BENCHMARK_CARD_PASS
```

Failure conditions:

- missing card;
- missing split strategy;
- missing contamination assessment;
- metric reported outside the benchmark card;
- dataset substitution without decision record.

## 9. Contamination Audit Requirement

The contamination audit MUST identify whether evaluation data could have leaked into model design, prompt logic, examples, fixtures, docs, or training-adjacent materials.

The audit MUST cover:

```text
source overlap
fixture overlap
documentation overlap
prompt-template overlap
example-output overlap
time-based leakage
manual selection bias
post-hoc threshold tuning
```

The audit MUST output:

```text
CONTAMINATION_AUDIT_PASS
CONTAMINATION_AUDIT_BLOCKED
CONTAMINATION_AUDIT_FAIL
```

Any high or unknown contamination risk MUST block benchmark-grade claims.

## 10. Domain-Distance Policy

Every output MUST be tagged with a domain regime:

```text
in_domain
adjacent_domain
out_of_domain
unknown_domain
```

Policy:

```text
in_domain + calibrated: probability MAY be emitted.
adjacent_domain: ordinal output SHOULD be used by default.
out_of_domain: probability MUST be suppressed.
unknown_domain: probability MUST be suppressed.
```

A domain-distance artifact MUST map each dataset and operating context to its allowed output mode.

Release gate:

```text
DOMAIN_DISTANCE_PASS
```

## 11. Resource-Effectiveness Requirement

Each full verification run MUST report:

```yaml
wall_time_seconds: number
cpu_time_seconds: number | null
peak_memory_mb: number | null
network_required: boolean
external_tools_required: string[]
number_of_tests: integer
number_of_gates: integer
expensive_failures: string[]
rerun_required: boolean
```

Accuracy without cost accounting is insufficient for institution-grade release.

Release gate:

```text
RESOURCE_EFFECTIVENESS_PASS
```

## 12. Product Claim Audit

A release MUST scan all public surfaces:

```text
README
package metadata
docs
OpenAPI
frontend copy
CLI help
API response strings
methodology endpoint
dossier renderer
```

The scanner MUST block unsupported claims, including:

```text
automatic person-status inference
unsupported probability language
unqualified reliability claims
cross-domain claims without artifact support
benchmark claims without contamination card
production-readiness claims without release gate evidence
```

Release gate:

```text
PRODUCT_CLAIM_AUDIT_PASS
```

## 13. Misuse and Human-Impact Threat Model

A formal threat model MUST be added before the score can exceed 8.0.

The threat model MUST include:

```text
misinterpretation risk
institutional over-reliance risk
false authority risk
selective evidence risk
cross-language extraction error risk
record-routing misuse risk
dossier misuse risk
interviewer question misuse risk
privacy and sensitive-data risk
```

For each risk, the document MUST include:

```yaml
risk_id: string
risk_description: string
affected_surface: string
severity: low | medium | high
likelihood: low | medium | high
mitigation: string
verification_gate: string
residual_risk: string
owner: string
```

## 14. Release Governance

### 14.1 Release states

```text
RESEARCH_ONLY
INTERNAL_ALPHA
CONTROLLED_REVIEW
INSTITUTION_GRADE_CANDIDATE
BENCHMARK_GRADE_CANDIDATE
```

COGVERITAS remains RESEARCH_ONLY until benchmark-card, contamination-audit, domain-distance, product-claim-audit, and misuse-threat-model gates pass.

### 14.2 Promotion rules

Promotion to INTERNAL_ALPHA requires:

```text
COGVERITAS_VERIFY_COMPLETE
VERIFY_RELEASE_PASS
BENCHMARK_CARD_PASS
PRODUCT_CLAIM_AUDIT_PASS
```

Promotion to CONTROLLED_REVIEW requires:

```text
DOMAIN_DISTANCE_PASS
RESOURCE_EFFECTIVENESS_PASS
MISUSE_THREAT_MODEL_PASS
```

Promotion to INSTITUTION_GRADE_CANDIDATE requires:

```text
EXTERNAL_REPLICATION_READY
CONTAMINATION_AUDIT_PASS
CROSS_DOMAIN_MATRIX_PASS
```

Promotion to BENCHMARK_GRADE_CANDIDATE requires independent reproduction by a separate environment or reviewer.

## 15. CI Gate Extensions

Add make targets:

```make
benchmark-card-check
contamination-audit
domain-distance-check
resource-effectiveness-check
product-claim-audit
misuse-threat-model-check
external-replication-check
institutional-verify
```

`make institutional-verify` MUST run:

```text
make cogveritas-verify
make verify-release
make benchmark-card-check
make contamination-audit
make domain-distance-check
make resource-effectiveness-check
make product-claim-audit
make misuse-threat-model-check
make external-replication-check
```

Expected terminal state:

```text
COGVERITAS_VERIFY_COMPLETE
VERIFY_RELEASE_PASS
BENCHMARK_CARD_PASS
CONTAMINATION_AUDIT_PASS
DOMAIN_DISTANCE_PASS
RESOURCE_EFFECTIVENESS_PASS
PRODUCT_CLAIM_AUDIT_PASS
MISUSE_THREAT_MODEL_PASS
EXTERNAL_REPLICATION_READY
INSTITUTIONAL_VERIFY_COMPLETE
```

## 16. Execution Roadmap

### PR-1: Benchmark Card and Contamination Audit

Deliverables:

```text
BENCHMARK_CARD.json
CONTAMINATION_AUDIT.json
benchmark-card-check
contamination-audit
```

Acceptance:

```text
No metric is accepted without benchmark card support.
Unknown contamination blocks benchmark-grade claims.
```

### PR-2: Domain-Distance Enforcement

Deliverables:

```text
DOMAIN_DISTANCE_POLICY.json
DOMAIN_DISTANCE_POLICY.md
domain-distance-check
```

Acceptance:

```text
Probability is suppressed outside calibrated in-domain regimes.
Every public output exposes allowed-use regime.
```

### PR-3: Resource-Effectiveness Audit

Deliverables:

```text
RESOURCE_EFFECTIVENESS.json
RESOURCE_EFFECTIVENESS.md
resource-effectiveness-check
```

Acceptance:

```text
Every full verification run reports time, cost, memory, external dependency, and expensive failures.
```

### PR-4: Product Claim Audit

Deliverables:

```text
PRODUCT_CLAIM_AUDIT.json
PRODUCT_CLAIM_POLICY.md
product-claim-audit
```

Acceptance:

```text
README, docs, UI, API, CLI, package metadata, and dossier surfaces cannot overclaim.
```

### PR-5: Misuse Threat Model

Deliverables:

```text
docs/security/MISUSE_THREAT_MODEL.md
misuse-threat-model-check
```

Acceptance:

```text
Every high-risk misuse surface has mitigation and verification gate.
```

### PR-6: External Replication Package

Deliverables:

```text
EXTERNAL_REPLICATION_READINESS.json
EXTERNAL_REPLICATION_GUIDE.md
external-replication-check
```

Acceptance:

```text
Fresh environment reproduction is documented.
Unavailable external data produces blocked state, not false success.
```

## 17. Institutional Definition of Done

The program is complete only when:

```text
institutional-verify passes
all required artifacts exist
all public surfaces pass product-claim audit
all metrics are linked to benchmark cards
all probabilities obey domain-distance policy
all known misuse risks have mitigation gates
fresh-environment reproduction is documented
obsolete scaffold PRs are closed or merged cleanly
```

## 18. Final Quality Rule

COGVERITAS may only claim higher maturity when its evidence boundary becomes stricter than its product language.

A higher score is not earned by adding features.
A higher score is earned by making unsupported claims impossible.
