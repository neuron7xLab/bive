# Industrial Release Package

This document defines the current GitHub-ready product package.

## Package layers

1. Core engine: transcript ingestion, evidence graph, hypotheses, questions, markdown report.
2. API: FastAPI contract, request IDs, API versioning, error envelope, readiness, metrics.
3. UI: operational console, safe DOM rendering, product/system/science/AOS panels.
4. Governance: threat model, Microsoft REST contract, operational excellence, release gates.
5. AOS layer: prompt kernel, eval harness, score schema, execution contracts.
6. Cognitive-control layer: excitation/inhibition weights, agent votes, fractal checks, reverse inference plan.
7. Neurocognitive protocol: CNS analogies mapped to mechanisms, validators, tests, and forbidden claims.
8. Product operating layer: positioning, jobs-to-be-done, activation path, metrics, readiness scorecard.

## Release rings

| Ring | Audience | Required gate | Claim |
|---|---|---|---|
| local | maintainer | `make verify` | local engineering candidate |
| package | maintainer | wheel smoke + manifest | installable Python package |
| public_github | open-source users | product-readiness + explicit unknowns | research/product candidate |
| production | controlled deployment | CVE audit + Docker + deployment smoke + human-impact review | only after external gates close |

## Required command sequence

```bash
python3 -m venv .venv
. .venv/bin/activate
make verify-bootstrap
make verify
make product-readiness
make wheel-smoke
make manifest-check
```

External gates:

```bash
make dependency-audit
make docker-build
make docker-run
```

## Product decision

Current status is `YELLOW`: GitHub release candidate allowed with explicit limitations; production deployment blocked until external gates close.
