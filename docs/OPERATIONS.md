# Operations Runbook

## Local verification

```bash
python -m venv .venv
. .venv/bin/activate
python3 -m venv .venv
. .venv/bin/activate
make verify-release
```

## Runtime modes

| Mode | `BIVE_ENV` | Auth | Intended use |
| --- | --- | --- | --- |
| local | `local` | optional | development and local demos |
| staging | `staging` | required | pre-production validation |
| production | `production` | required | controlled deployment |

## Required production variables

- `BIVE_ENV=production`
- `BIVE_API_TOKEN=<secret>`
- `BIVE_STORAGE=<writable sqlite path>`
- `BIVE_MAX_UPLOAD_BYTES=<positive int>`
- `BIVE_MAX_SEGMENTS=<positive int>`
- `BIVE_MAX_TEXT_CHARS=<positive int>`

## Health endpoints

- `/health`: service metadata.
- `/livez`: process liveness.
- `/readyz`: configuration and storage readiness.
- `/metrics`: minimal Prometheus-style counters.

## Incident rule

If `/readyz` is non-200, the service is not production-ready. Do not hide this behind a green `/health` check, because that is how software lies politely before failing loudly.
