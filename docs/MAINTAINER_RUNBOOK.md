# Maintainer Runbook

## Before merge

```bash
python3 -m venv .venv
. .venv/bin/activate
make verify-release
```

## Before release archive

```bash
make clean
make openapi
make manifest
make verify-release
python -m build
```

## Dependency/security review

```bash
make dependency-audit
make license-audit
```

If network access is unavailable, record `UNKNOWN_SECURITY_STATE` in the release notes.

## Version update checklist

- `pyproject.toml`
- `src/bive/__init__.py`
- `README.md`
- `SOURCE_REGISTRY.yaml`
- `CHANGELOG.md`
- `ARTIFACT_MANIFEST.json` after `make manifest`
