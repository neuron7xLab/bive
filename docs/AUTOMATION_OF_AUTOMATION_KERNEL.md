# Automation-of-Automation Kernel

## System role

The Automation-of-Automation layer manufactures verified delegations. It does not promise intelligence. It produces contracts, gates, logs, failure modes, and evidence bundles.

## Required modules

1. Intent Compiler
2. Process Modeler
3. Automation Boundary Engine
4. Tool Contract Generator
5. Workflow Generator
6. Sandbox Executor
7. Verifier
8. Repair Engine
9. Template Registry
10. Governance Engine

## Execution invariant

No workflow is accepted unless it has:

- trigger;
- input;
- rule;
- action;
- output;
- verification;
- log;
- failure path;
- rollback or stop condition;
- evidence artifact.

## Dynamic environment behavior

When dependencies drift, APIs fail, inputs mutate, network access disappears, or permissions change, AOS must fail closed. The correct status is not optimism. The correct status is the smallest honest operational state: `BLOCKED`, `UNKNOWN`, `RED`, or `HUMAN_REVIEW_REQUIRED`.

## Maintenance loop

`DETECT → LOCALIZE → EXPLAIN → PATCH → RE-RUN → COMPARE → REGRESSION → RECORD`

The repository validates this layer through `make aos-kernel`, eval fixtures, and tests covering risk classification, contract generation, score semantics, and package resource loading.
