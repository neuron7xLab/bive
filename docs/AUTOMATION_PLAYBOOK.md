# Automation Playbook

BIVE automation is organized around fail-closed release evidence.

## Local loop

```bash
python3 -m venv .venv
. .venv/bin/activate
make verify-release
```

This runs repo hygiene, metadata, dependency contracts, test architecture, bibliography, lint, typecheck, coverage, schemas, API smoke, frontend checks, science registry, dynamic probe, OpenAPI, static security, wheel smoke, manifest and evidence bundle.

## Networked release host

```bash
make dependency-audit
make license-audit
make docker-build
make docker-run
```

Dependency CVE and Docker runtime gates require network/Docker host access. If unavailable, their status must remain `UNKNOWN`.

## GitHub automation

- Matrix release gate on Python 3.10/3.11/3.12.
- Dependency Review on pull requests.
- OpenSSF Scorecard on pushes.
- Artifact upload for verification logs and JSON evidence.

## Evidence bundle

```bash
make evidence-bundle
```

The evidence bundle records hashes for core release artifacts and validation outputs.
