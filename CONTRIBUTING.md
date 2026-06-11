# Contributing

BIVE accepts changes only when they preserve the core invariant: the system must produce reviewable evidence, uncertainty, counter-evidence and missing-evidence questions, not automatic person-level accusations.

## Required local gate

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev,api]'
make verify-release
```

## Pull request rules

- Add or update tests for behavior changes.
- Update schemas when JSON/API contracts change.
- Update docs when commands, boundaries, configuration or release gates change.
- Do not add language that claims lie detection, guilt, certainty or automated judgment.
- Keep optional media/ML adapters optional; the core package must remain lightweight.
- Include command output or artifacts for every production-impacting claim.

## Development commands

```bash
make test
make lint
make typecheck
make schema
make api-smoke
make wheel-smoke
make metadata
make manifest-check
```
