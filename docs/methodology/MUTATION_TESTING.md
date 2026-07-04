# Mutation Testing

Closes the A3/A4 gap: coverage is *visibility*, not correctness. A green test proves
nothing unless it can **fail** on a plausible defect. Enforced by
`scripts/mutation_check.py` (`MUTATION_SCORE_PASS`), which writes
`artifacts/verification/MUTATION_SCORE.json`.

## What it does

For each crown-jewel invariant it applies a known semantic mutation to the real
source, runs the covering test, and requires the test to **fail** (the mutant is
*killed*). A mutation the suite does not catch is a **survivor** — a hole in the
evidence — and is named; the gate fails on any survivor.

| Mutation | Invariant | Covering test |
|---|---|---|
| disable the forbidden-judgment scan | no person-level judgment in system framing | `test_no_forbidden_person_level_strings` |
| let probability escape out of domain | unsupported probability suppressed (ECE gate) | `test_no_float_probability_when_ece_fails` |
| classify everything checkable | opinion is not externally checkable | `test_opinion_markers_are_language_specific` |

## Guarantees

- **Bulletproof revert:** each mutation is applied and reverted in a `finally`; the
  source is never left mutated (proven by `test_source_is_reverted_after_a_mutation_run`).
- **The gate itself is falsifiable:** `test_gate_detects_a_survivor` forces the
  killer to pass and confirms the gate reports a survivor.
- **Target drift is caught:** a mutation whose target string is absent is
  `invalid_mutation`, not a false PASS.

## Enforcement

`make mutation-check` and the `institutional-verify` roadmap. **Not** in
`verify-release`: it mutates source during the run and must never execute inside the
release battery.

## Boundary

This is a *targeted* mutation battery on the critical invariants, not full-project
mutation coverage. It proves the crown-jewel tests are defect-sensitive; it does not
claim every line is mutation-covered. `MUTATION_SCORE.json` is regenerated each run
(the gate, not the file, is the source of truth) and is gitignored.
