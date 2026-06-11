# PR Merge Protocol

## Required before merge

```bash
make verify
```

The PR is blocked if any of these fail:

1. Python package import.
2. Unit tests.
3. Schema parse.
4. Report invariant validation.
5. PR gate.
6. Required docs present.
7. No generated report contains person-level verdict terms.

## Pull request checklist

- [ ] Adds or updates tests.
- [ ] Updates docs when behavior changes.
- [ ] Adds provenance for new evidence events.
- [ ] Does not add a “liar/guilty” automated label.
- [ ] Includes limitations and counter-evidence paths.
- [ ] Keeps heavy multimedia tools optional unless explicitly isolated.
- [ ] Keeps demo runnable without private data.

## GitHub commands

```bash
bive analyze --input samples/demo_transcript.json --output artifacts/demo_report.json
bive validate --input artifacts/demo_report.json
bive render --input artifacts/demo_report.json --output artifacts/demo_report.md
bive-pr-check --repo .
```
