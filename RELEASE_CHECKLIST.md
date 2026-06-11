# Release Checklist

A release is blocked unless every checked item has machine evidence.

- [ ] `make clean`
- [ ] `pip install -e '.[dev,api]'
- [ ] `make verify-release`
- [ ] `make dependency-audit` or documented `UNKNOWN_SECURITY_STATE` waiver
- [ ] `make openapi`
- [ ] `make manifest`
- [ ] `python -m build`
- [ ] wheel smoke from clean venv
- [ ] Docker build and readiness smoke in an environment with Docker
- [ ] `ARTIFACT_MANIFEST.json` regenerated
- [ ] `TEST_RESULT.md` updated from current logs
- [ ] tag version matches `pyproject.toml`, `src/bive/__init__.py`, README and manifest
