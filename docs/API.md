# BIVE API

BIVE exposes a FastAPI service and a static operational UI. The API returns structured reports, evidence events, hypotheses, limitations and verification questions. It does not return automatic person-level lie, guilt or truth verdicts.

## Run

```bash
make api
# open http://127.0.0.1:8080
```

## Runtime endpoints

- `GET /health` — service status, version and safety invariant flags.
- `GET /livez` — process liveness.
- `GET /readyz` — configuration and storage readiness.
- `GET /metrics` — Prometheus-style counters for requests, 5xx errors and latency sum.
- `GET /api/v1/capabilities` — modalities, outputs, gates and optional adapters.
- `GET /api/v1/system/status` — operational state, limits, storage counts and release gates.
- `GET /api/v1/system/design-contract` — backend/frontend/security/evidence contract exposed for the UI.

## Report endpoints

- `POST /api/v1/reports/from-transcript` — create verification report from transcript JSON.
- `GET /api/v1/reports` — list stored reports.
- `GET /api/v1/reports/{report_id}` — fetch report JSON.
- `GET /api/v1/reports/{report_id}/markdown` — render report as Markdown.

In `production` or `staging`, report endpoints require `Authorization: Bearer <token>` or `x-bive-api-key: <token>`.

## Request shape

```json
{
  "subject_scope": "public_statement_review",
  "segments": [
    {"speaker": "subject", "start": 0, "end": 4.1, "text": "Я точно ніколи не мав доступу."}
  ]
}
```

## Runtime constraints

- Extra fields are rejected by Pydantic strict models.
- Upload size is limited by `BIVE_MAX_UPLOAD_BYTES`.
- Segment count is limited by `BIVE_MAX_SEGMENTS`.
- Segment text length is limited by `BIVE_MAX_TEXT_CHARS`.
- API responses include `X-Request-ID` and `X-BIVE-Version`.
- Security headers include content-type, frame, referrer, permissions and CSP boundaries.

## Error envelope

```json
{
  "error": "validation_error",
  "details": ["String should have at least 1 character"],
  "request_id": "client-or-server-generated-id"
}
```

## OpenAPI

The versioned OpenAPI artifact is `docs/openapi.json` and is checked by `make openapi`.

## Microsoft-style API contract

All `/api/v1/*` operations require `api-version=2026-06-11`. Error responses use the nested `{ "error": { "code", "message", "details", "innererror" } }` envelope and propagate `x-ms-request-id`.
