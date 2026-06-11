# Test Strategy

BIVE tests must prove contracts, not decorate confidence.

## Required layers

1. Unit invariants: models, graph, calibration, linguistic extraction, report rendering.
2. API contract: schema strictness, auth boundary, limits, error envelope, security headers.
3. CLI contract: controlled failures, no normal-mode traceback, stable exit codes.
4. Storage contract: schema version, concurrency, healthcheck, audit log.
5. Frontend static contract: no unsafe dynamic HTML insertion, packaged UI assets, accessible operational sections.
6. Science/bibliography contract: bounded references, negative claim boundaries, no lie-detector claim drift.
7. Dynamic environment probe: repeated runs, malformed input, oversized payload, production auth, concurrent storage writes.
8. Release automation contract: Makefile, CI workflow and release script remain synchronized.

## Gates

```bash
make test
make test-slow
make coverage
make test-architecture
make dynamic-probe
make verify-release
```

## Minimum bar

- Test architecture gate requires at least 70 test functions.
- Coverage gate requires at least 80% line coverage on non-slow tests; slow integration probes are executed as explicit release gates.
- Critical production claims require a direct test or validation script.
- Any test bypass must be documented as a release waiver, not silently skipped.
