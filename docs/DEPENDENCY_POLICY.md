# Dependency Policy

BIVE uses dependency contracts because “works on my machine” is not a release strategy, just a confession with extra steps.

## Surfaces

- `core`: library and CLI runtime, minimal dependency surface.
- `api`: FastAPI/UI runtime.
- `dev`: tests, lint, typecheck, build and metadata validation.
- `security`: static security, vulnerability audit, SBOM and license inventory.
- `media`, `ml`, `ops`: optional extension surfaces; never required for the core release gate.

## Files

- `pyproject.toml`: canonical package metadata and dependency ranges.
- `requirements/*.in`: human-maintained install intent.
- `constraints/py310.txt`: known-good pinned graph for the current packaging pass.
- `scripts/validate_dependency_contracts.py`: offline dependency contract gate.

## Commands

```bash
make dependency-contracts
make deps-compile
make dependency-audit
make license-audit
```

## Release rule

A release may pass local gates with dependency CVE state marked `UNKNOWN` only when network access is unavailable and the artifact records that failure. A public GitHub release requires successful `pip-audit` or an explicit waiver with expiry.

## Compiled requirement contracts

Open-source release candidates must include both intent files (`requirements/*.in`) and locked release intent files (`requirements/*.txt`). The validator rejects missing compiled requirement surfaces because dependency governance without actual lock artifacts is just theatre with filenames.
