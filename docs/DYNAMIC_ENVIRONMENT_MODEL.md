# Dynamic Environment Model

BIVE is treated as a changing runtime system, not a static demo. Dynamic operation means the same code must remain safe when inputs change, users repeat runs, storage receives concurrent writes, API payloads exceed budgets, deployment mode changes, optional adapters fail, and external dependency status becomes unknown.

## Runtime invariants

1. **Fail closed in production/staging.** If `BIVE_ENV=production` or `BIVE_ENV=staging`, API write/read routes require `BIVE_API_TOKEN`.
2. **No unbounded input.** Upload size, segment count and text length are bounded before expensive processing.
3. **No person-level verdict.** The system emits evidence, uncertainty, missing evidence and review questions; it must not emit liar/guilt/intent/diagnosis decisions.
4. **State is observable.** `/readyz`, `/metrics`, `/api/v1/system/status`, storage stats and release gates expose current operational condition.
5. **Repeated runs are structurally stable.** Runtime report IDs may differ; normalized structural fields must remain stable for the same input and version.
6. **Storage tolerates concurrency.** SQLite uses WAL and busy timeout; concurrent writes are covered by regression tests and dynamic probes.
7. **Scientific claims are bounded.** The science registry maps disciplines to allowed and blocked claims.

## Dynamic probes

Run:

```bash
make dynamic-probe
```

The probe checks:

- valid transcript baseline;
- repeated-run structural hash stability;
- malformed input rejection;
- oversized payload rejection;
- production auth fail-closed behavior;
- concurrent storage writes;
- science registry load and minimum reference depth.

Output artifact:

```text
artifacts/verification/DYNAMIC_ENVIRONMENT_PROBE.json
```

## Failure response policy

- malformed input: controlled `BIVE_ERROR` or JSON error envelope;
- oversized API payload: `413` or `422`;
- missing production token: `401` or `503`;
- storage failure: readiness becomes `not_ready`;
- unavailable dependency audit: release state remains `UNKNOWN`, not `PASS`.
