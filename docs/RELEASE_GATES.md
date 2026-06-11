# Release Gates

A release is not approved by documentation. It is approved by passing commands.

## Mandatory local gate

```bash
python3 -m venv .venv
. .venv/bin/activate
make verify-release
```

## Gate composition

| Gate | Purpose |
| --- | --- |
| `repo-clean` | block caches, local DBs and generated junk |
| `metadata` | synchronize pyproject, README, package version and manifest |
| `lint` | static syntax/style defects |
| `typecheck` | typed API/code contract |
| `test` | unit and contract behavior |
| `coverage` | minimum behavioral coverage |
| `schema` | JSON schema and fixture validation |
| `openapi` | API contract export/check |
| `api-smoke` | API runtime smoke |
| `wheel-smoke` | production wheel install/import/runtime check |
| `security-static` | static security scan |
| `manifest-check` | release artifact integrity |

## External gates

- `make dependency-audit`: requires advisory network access.
- `make docker-build`: requires Docker.

If an external gate cannot run, release state is `UNKNOWN` for that dimension.

## Microsoft hardening gates

Stage 8 adds `threat-model`, `microsoft-rest`, and `operational-excellence` gates to close SDL, REST correlation/versioning and service-operation evidence gaps.
