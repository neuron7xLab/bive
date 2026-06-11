# Dependency contracts

BIVE separates dependency intent from resolved dependency evidence:

- `*.in` files define install surfaces: `core`, `api`, `dev`, `security`, `prod`.
- `constraints/py310.txt` pins the known-good Python 3.10-compatible graph observed for this release packaging pass.
- `make deps-check` validates the dependency contract without network access.
- `make deps-compile` refreshes pinned requirements when network access is available.
- `make dependency-audit` must run in CI or a networked release host; if PyPI/advisory lookup is unavailable, release state remains `UNKNOWN`, not `PASS`.

Do not add an optional dependency directly to docs without updating `pyproject.toml`, the matching `requirements/*.in`, and the dependency validation gate.
