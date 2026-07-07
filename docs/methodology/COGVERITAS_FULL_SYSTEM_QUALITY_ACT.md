# COGVERITAS Full System Quality Act

Version: 1.0
Status: Master execution act
Mode: fail-closed
Repository: neuron7xLab/bive
Owner: neuron7xLab
Scope: institutional-grade evidence-review system

## 1. Executive Decision

COGVERITAS is not complete when the repository has many features.

COGVERITAS is complete only when every feature is bounded by evidence, every metric is reproducible, every public claim is audited, every output exposes its limitation, and every unsupported conclusion is structurally impossible.

The system must become harder to misuse than to use correctly.

## 2. Core Product Boundary

COGVERITAS is an external-checkability and evidence-review system.

It MAY:

- extract claims from testimony or transcript text;
- classify claims by external checkability;
- preserve provenance for every claim;
- identify missing anchors such as time, place, actors, records, or amounts;
- route claims to external record types;
- build timelines from anchored claims;
- flag review-worthy inconsistencies;
- generate interviewer follow-up questions that elicit checkable detail;
- export an analyst dossier;
- report calibration state and limitations;
- block unsupported probabilities.

It MUST NOT:

- decide person-level truth status;
- produce a person-level verdict;
- present itself as an automatic adjudication system;
- emit unsupported probabilities;
- treat internal narrative coherence as evidence;
- treat green CI as product validity;
- use benchmark numbers without benchmark cards;
- claim cross-domain reliability without cross-domain artifacts.

## 3. Current Honest Maturity

Current maturity is not elite.

```text
Current band: 6.5-7.0 / 10
Class: strong internal research-product prototype
Target band: 8.0+ institution-grade candidate
Final target: 9.0+ externally replicated benchmark-grade candidate
```

The score cannot increase by feature count. It can only increase by stronger controls.

## 4. System Architecture Layers

The full system is decomposed into nine layers.

```text
L1  Input ingestion
L2  Language and claim extraction
L3  External-checkability tagging
L4  Provenance and evidence graph
L5  Corroboration worklist
L6  Timeline and inconsistency review
L7  Analyst dossier and UI surfaces
L8  Evaluation, calibration, and benchmark governance
L9  Release, misuse, and external replication governance
```

Each layer must define:

```text
input
transform
output
known failure mode
artifact
release gate
owner
```

No layer may be treated as complete without an artifact and gate.

## 5. Non-Negotiable Invariants

```text
verdict = null
missing artifact = fail
unsupported probability = suppressed
unknown domain = ordinal-only output
unavailable external data = blocked state, not success
public claim stronger than evidence = release blocked
high headline metric without leakage control = invalid
```

These are not user preferences. They are system law.

## 6. Capability Registry

The repository must maintain a machine-readable capability registry.

Minimum capability fields:

```yaml
capability_id: string
name: string
status: proposed | experimental | validated_internal | externally_replicated | deprecated
intended_use: string
non_goals: string[]
input_contract: string
output_contract: string
required_artifacts: string[]
required_tests: string[]
release_gate: string
known_failure_modes: string[]
owner: string
```

Initial capability set:

```text
CV-C1  Transcript ingestion
CV-C2  Language-aware claim extraction
CV-C3  External-checkability tagging
CV-C4  Provenance graph
CV-C5  Corroboration worklist routing
CV-C6  Timeline construction
CV-C7  Review-worthy inconsistency detection
CV-C8  Analyst dossier export
CV-C9  Interview questions for missing checkable detail
CV-C10 Benchmark and contamination governance
CV-C11 Domain-distance policy
CV-C12 Product claim audit
CV-C13 Misuse threat model
CV-C14 External replication package
```

A capability cannot be called production-ready until its release gate passes.

## 7. Required Evidence Artifacts

The following artifacts are mandatory for institution-grade status:

```text
artifacts/verification/BENCHMARK_CARD.json
artifacts/verification/CONTAMINATION_AUDIT.json
artifacts/verification/CROSS_DOMAIN_MATRIX.json
artifacts/verification/DOMAIN_DISTANCE_POLICY.json
artifacts/verification/RESOURCE_EFFECTIVENESS.json
artifacts/verification/PRODUCT_CLAIM_AUDIT.json
artifacts/verification/MISUSE_THREAT_MODEL_AUDIT.json
artifacts/verification/EXTERNAL_REPLICATION_READINESS.json
artifacts/verification/CAPABILITY_REGISTRY.json
artifacts/verification/INSTITUTIONAL_SCORECARD.json
```

A release without these artifacts remains research-only.

## 8. Required Documents

```text
docs/methodology/BENCHMARK_CARD.md
docs/methodology/CONTAMINATION_AUDIT.md
docs/methodology/CROSS_DOMAIN_MATRIX.md
docs/methodology/DOMAIN_DISTANCE_POLICY.md
docs/methodology/RESOURCE_EFFECTIVENESS.md
docs/methodology/PRODUCT_CLAIM_POLICY.md
docs/security/MISUSE_THREAT_MODEL.md
docs/methodology/EXTERNAL_REPLICATION_GUIDE.md
docs/methodology/CAPABILITY_REGISTRY.md
docs/methodology/INSTITUTIONAL_SCORECARD.md
```

## 9. Benchmark Governance

Every metric must be bound to a benchmark card.

A benchmark card must include:

```yaml
benchmark_name: string
version: string
task_type: string
data_source: string
access_date: string | null
license_notes: string
sample_count: integer | null
split_strategy: string
grouping_strategy: string | null
known_leakage_risks: string[]
contamination_risk: low | medium | high | unknown
metrics: string[]
calibration_policy: string
limitations: string[]
reproduction_command: string
artifact_sha256: string
```

No metric may appear in README, docs, API, UI, or package metadata unless it is traceable to a benchmark card.

## 10. Contamination Audit

The contamination audit must search for:

```text
source overlap
fixture overlap
prompt-example overlap
documentation leakage
post-hoc threshold tuning
manual selection bias
stale benchmark reuse
data substitution without decision record
high metric without transfer validation
```

Rules:

```text
unknown contamination = benchmark-grade blocked
high metric without cross-domain support = capability claim blocked
metric without limitation = invalid
```

## 11. Domain-Distance Policy

Every output must expose its allowed-use regime.

```text
in_domain        -> probability may be allowed only if calibrated
adjacent_domain  -> ordinal output by default
out_of_domain    -> probability suppressed
unknown_domain   -> probability suppressed
```

Required fields in every public output:

```yaml
domain_regime: in_domain | adjacent_domain | out_of_domain | unknown_domain
calibration_state: calibrated | uncalibrated | unavailable
probability_allowed: boolean
limitation_summary: string
next_verification_step: string
```

## 12. Resource-Effectiveness Audit

Every institutional verification run must report:

```yaml
wall_time_seconds: number
cpu_time_seconds: number | null
peak_memory_mb: number | null
network_required: boolean
external_tools_required: string[]
number_of_tests: integer
number_of_gates: integer
number_of_artifacts_checked: integer
expensive_failures: string[]
rerun_required: boolean
```

A system that passes only by unlimited runtime, hidden manual intervention, or fragile retries is not institution-grade.

## 13. Product Claim Audit

The release scanner must inspect:

```text
README
pyproject metadata
OpenAPI
API response strings
CLI help
frontend copy
dossier renderer
methodology endpoint
docs
release notes
```

Blocked claim categories:

```text
person-level adjudication
unsupported probability
unqualified reliability
cross-domain capability without artifact
benchmark claim without benchmark card
production readiness without release gates
scientific claim without source or artifact
```

Product language must be weaker than the evidence, never stronger.

## 14. Misuse and Human-Impact Threat Model

The threat model must include at least:

```text
misinterpretation risk
over-reliance risk
false authority risk
selective-evidence risk
cross-language extraction error
record-routing misuse
dossier misuse
interview-question misuse
privacy and sensitive-data risk
institutional escalation risk
```

Each risk must define:

```yaml
risk_id: string
affected_surface: string
severity: low | medium | high
likelihood: low | medium | high
mitigation: string
verification_gate: string
residual_risk: string
owner: string
```

No controlled-review release is allowed without this document and audit artifact.

## 15. External Replication Package

The replication package must support a fresh environment.

It must include:

```text
one-command setup
one-command verification
dataset access notes
expected artifact list
expected terminal output
known unavailable-data behavior
container or lockfile evidence
independent reviewer checklist
```

Unavailable external data must produce a blocked state, not false success.

## 16. Institutional CI Gates

Add or enforce these gates:

```make
benchmark-card-check
contamination-audit
cross-domain-matrix-check
domain-distance-check
resource-effectiveness-check
product-claim-audit
misuse-threat-model-check
external-replication-check
capability-registry-check
institutional-scorecard-check
institutional-verify
```

`make institutional-verify` must run:

```text
make cogveritas-verify
make verify-release
make benchmark-card-check
make contamination-audit
make cross-domain-matrix-check
make domain-distance-check
make resource-effectiveness-check
make product-claim-audit
make misuse-threat-model-check
make external-replication-check
make capability-registry-check
make institutional-scorecard-check
```

Expected terminal state:

```text
COGVERITAS_VERIFY_COMPLETE
VERIFY_RELEASE_PASS
BENCHMARK_CARD_PASS
CONTAMINATION_AUDIT_PASS
CROSS_DOMAIN_MATRIX_PASS
DOMAIN_DISTANCE_PASS
RESOURCE_EFFECTIVENESS_PASS
PRODUCT_CLAIM_AUDIT_PASS
MISUSE_THREAT_MODEL_PASS
EXTERNAL_REPLICATION_READY
CAPABILITY_REGISTRY_PASS
INSTITUTIONAL_SCORECARD_PASS
INSTITUTIONAL_VERIFY_COMPLETE
```

## 17. Institutional Scorecard

The repository score must be computed from gates, not opinion.

```yaml
architecture_discipline:
  weight: 10
  source: capability registry + contracts
risk_governance:
  weight: 15
  source: threat model + release governance
metric_validity:
  weight: 15
  source: benchmark card + contamination audit
cross_domain_evidence:
  weight: 10
  source: cross-domain matrix + domain-distance policy
ci_release_discipline:
  weight: 10
  source: verify-release + institutional-verify
data_reproducibility:
  weight: 15
  source: external replication package
resource_effectiveness:
  weight: 10
  source: resource-effectiveness artifact
product_claim_control:
  weight: 15
  source: product claim audit
```

Maturity bands:

```text
0-5.9   prototype
6.0-6.9 strong internal research prototype
7.0-7.9 credible product-research system
8.0-8.9 institution-grade candidate
9.0-10  externally replicated benchmark-grade system
```

No manual score override is allowed.

## 18. Execution Roadmap

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
Every metric is linked to a benchmark card.
High or unknown contamination blocks benchmark-grade claims.
```

### PR-2: Cross-Domain Matrix and Domain-Distance Policy

Deliverables:

```text
CROSS_DOMAIN_MATRIX.json
DOMAIN_DISTANCE_POLICY.json
DOMAIN_DISTANCE_POLICY.md
domain-distance-check
```

Acceptance:

```text
Every output has domain regime and allowed-use mode.
Probability is suppressed outside calibrated in-domain regimes.
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
Every institutional run reports time, memory, dependencies, tests, gates, artifacts, and expensive failures.
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
No public surface may overclaim relative to evidence.
```

### PR-5: Misuse Threat Model

Deliverables:

```text
docs/security/MISUSE_THREAT_MODEL.md
MISUSE_THREAT_MODEL_AUDIT.json
misuse-threat-model-check
```

Acceptance:

```text
Every high-risk public surface has mitigation and residual-risk record.
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
Fresh environment reproduction is documented and unavailable data fails closed.
```

### PR-7: Capability Registry and Institutional Scorecard

Deliverables:

```text
CAPABILITY_REGISTRY.json
INSTITUTIONAL_SCORECARD.json
capability-registry-check
institutional-scorecard-check
```

Acceptance:

```text
Maturity score is computed only from passing gates.
```

## 19. Release States

```text
RESEARCH_ONLY
INTERNAL_ALPHA
CONTROLLED_REVIEW
INSTITUTION_GRADE_CANDIDATE
BENCHMARK_GRADE_CANDIDATE
```

Promotion rules:

```text
RESEARCH_ONLY -> INTERNAL_ALPHA:
  cogveritas-verify + verify-release + benchmark-card + product-claim-audit

INTERNAL_ALPHA -> CONTROLLED_REVIEW:
  domain-distance + resource-effectiveness + misuse-threat-model

CONTROLLED_REVIEW -> INSTITUTION_GRADE_CANDIDATE:
  cross-domain-matrix + contamination-audit + external-replication-ready

INSTITUTION_GRADE_CANDIDATE -> BENCHMARK_GRADE_CANDIDATE:
  independent reproduction by a separate environment or reviewer
```

## 20. Final Definition of Done

COGVERITAS reaches institution-grade only when:

```text
institutional-verify passes
all required artifacts exist
all public claims are audited
all metrics are benchmark-card bound
all contamination risks are classified
all outputs have domain regime
all unsupported probabilities are suppressed
all misuse risks have mitigation gates
all capabilities have registry entries
all scores are computed from gates
fresh-environment reproduction is documented
obsolete scaffold PRs are closed or merged cleanly
```

## 21. Final System Law

A mature verification system is not the one that says more.

It is the one that refuses to say what it cannot prove.

COGVERITAS becomes higher-level only when unsupported claims become structurally impossible.
