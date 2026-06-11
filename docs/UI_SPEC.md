# BIVE UI Specification

## Product intent

The UI is an operational console for evidence-first behavioral verification. It is not a marketing landing page and not a lie-detector toy. The primary user action is to submit structured transcript JSON and inspect a reproducible report.

## Information architecture

1. Hero: product identity, action entry, system readiness.
2. Metrics rail: readiness, report count, auth mode, runtime limits, release gates, latency sum.
3. Architecture cards: backend, frontend, governance.
4. Analysis console: token, payload, demo, run, health, export actions.
5. Result grid: report summary, evidence graph, hypotheses, human review questions.
6. Operational contract: gates, capabilities, design contract.
7. Raw output: JSON and Markdown report.

## Interaction states

- idle: no report built;
- busy: analysis request in progress;
- ok: status/report command completed;
- error: validation, auth, network, or runtime failure.

## Safety and clarity rules

- Do not display person-level guilt, lie, or legal verdicts.
- Show missing evidence and human-review questions.
- Preserve raw machine output for auditability.
- Keep operational unknowns visible.
- Do not rely on color alone for pass/fail meaning.

## Frontend quality gate

`scripts/check_frontend_quality.py` enforces:

- semantic root markers;
- labels and status live region;
- API-token flow;
- system-status integration;
- report rendering function;
- safe DOM rendering tokens;
- no `innerHTML`, `outerHTML`, or `insertAdjacentHTML`;
- responsive CSS and reduced-motion support.
