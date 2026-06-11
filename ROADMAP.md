# Roadmap

## Current stage: open-source productized research engine

- Keep core deterministic and lightweight.
- Preserve safety boundary: evidence review, not automated accusation.
- Maintain reproducible local, wheel and API verification.
- Treat optional multimodal adapters as isolated extensions.

## Next hardening targets

1. Complete authenticated multi-tenant API boundary.
2. Add persistent audit-log export and retention controls.
3. Add concurrency and SQLite migration tests at stress scale.
4. Add dependency lockfile and SBOM publishing in CI.
5. Add Docker runtime verification in CI.
6. Add benchmark regression budgets for large transcript workloads.
