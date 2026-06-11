# AOS Prompt OS

BIVE Stage 9 embeds `AOS-PROMPT-KERNEL v1.0` as an operational prompt operating system, not as decorative prose.

## Purpose

AOS converts ambiguous human intent into bounded executable delegation:

`INTENT → BOUNDARY → CONTRACT → EXECUTION → VERIFICATION → EVIDENCE → STATUS`

The repository treats the prompt kernel as a versioned artifact with eval tasks, scoring schema, templates, validators, CLI access, API visibility, and release gates.

## Files

- `prompts/AOS_PROMPT_KERNEL_v1.0.txt` — canonical prompt kernel.
- `data/aos/aos_kernel_contract.json` — machine-readable contract.
- `evals/aos_eval_tasks.json` — 20-task eval harness.
- `evals/aos_score_schema.json` — 10-metric scoring schema.
- `contracts/tool_contract_template.yaml` — agent tool contract template.
- `contracts/execution_contract_template.yaml` — execution contract template.
- `contracts/workflow_contract_template.yaml` — workflow contract template.
- `src/bive/aos.py` — runtime primitives for risk, status, intent, score, contract.
- `src/bive/aos_cli.py` — CLI interface.
- `scripts/validate_aos_kernel.py` — fail-closed repository validator.

## Runtime commands

```bash
make aos-kernel
bive-aos status
bive-aos compile "Automate this repository release with human approval gates"
```

## Status semantics

AOS never upgrades a specified contract to executed evidence. A missing log, failed tool, missing dependency, blocked network, or unavailable host capability produces `UNKNOWN`, `BLOCKED`, or `HUMAN_REVIEW_REQUIRED`; it does not produce fake `GREEN`.

## Product boundary

AOS is an automation governance layer. It does not autonomously deploy, delete, send, spend, or modify public systems without a risk classification and human gate. L5 unbounded autonomy is forbidden by default.
