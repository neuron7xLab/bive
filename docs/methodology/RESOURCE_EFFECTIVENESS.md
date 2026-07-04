# Resource-Effectiveness Audit

Implements the mandate's PR-3. Enforced by `scripts/resource_effectiveness_check.py`
(`RESOURCE_EFFECTIVENESS_PASS`), which writes
`artifacts/verification/RESOURCE_EFFECTIVENESS.json`.

An institutional run reports not only *whether* gates pass, but the **cost** of
reaching that result — wall time, dependency posture, test and gate counts, the
artifact set, and any expensive failures — so verification growth is visible and
bounded, never silent.

## What is reported and enforced

| field | source | enforced |
|---|---|---|
| per-gate wall time | `artifacts/verification/RELEASE_TIMINGS.json` | per-gate budget (600 s) |
| total wall time | sum of gate durations | total budget (1800 s) |
| slowest gates | ranked from gates.json | surfaced |
| memory policy | pinned deps / no-network core | reported |
| dependencies | lockfiles (`requirements/`) | reported |
| tests / gates | counts | reported |
| artifacts | required-artifact set | reported |
| expensive failures | non-passing gates + excerpt | surfaced, fails the gate |

## Budgets

```text
total battery  <= 1800 s
any single gate <= 600 s
any non-passing gate in the timing => fail
```

## Failure mode

If the timing artifact (`gates.json`) is missing, the gate fails (run `verify-release`
first). If the battery exceeds budget or any gate is non-passing, the report records
`status: FAIL` and the gate exits non-zero. Missing artifact = fail.

## Boundary

The report is regenerated each run (per-run wall time is non-reproducible) and is not
pinned. The gate, not the committed file, is the source of truth.
