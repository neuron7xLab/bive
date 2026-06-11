# Deployment

## Local development

```bash
python -m venv .venv
. .venv/bin/activate
python3 -m venv .venv
. .venv/bin/activate
make verify-release
make api
```

## Production process

```bash
python -m venv .venv
. .venv/bin/activate
pip install '.[api]'
export BIVE_ENV=production
export BIVE_API_TOKEN='replace-with-real-secret'
export BIVE_STORAGE='/var/lib/bive/bive.sqlite3'
bive-api
```

## Docker

```bash
export BIVE_API_TOKEN='replace-with-real-secret'
docker compose up --build
```

## Health and readiness

```bash
curl -f http://127.0.0.1:8080/livez
curl -f http://127.0.0.1:8080/readyz
curl -f http://127.0.0.1:8080/metrics
```

`/readyz` is the production readiness endpoint. `/health` is metadata only.

## Required release evidence

```bash
make verify-release
make dependency-audit
make docker-build
```

If network or Docker is unavailable, that gate remains `UNKNOWN`, not `PASS`.
