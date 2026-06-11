# Backend / Frontend Contract

## Runtime contract

The shipped UI is a vanilla single-page operational console served by FastAPI from packaged wheel assets. It must function without Node, bundlers, npm, external fonts, CDN assets, or hidden local state.

## Backend endpoints consumed by the UI

- `GET /health`
- `GET /livez`
- `GET /readyz`
- `GET /metrics`
- `GET /api/v1/capabilities`
- `GET /api/v1/system/status`
- `GET /api/v1/system/design-contract`
- `GET /api/v1/system/interface-contract`
- `POST /api/v1/reports/from-transcript`
- `GET /api/v1/reports/{report_id}/markdown`

## Authentication contract

Local mode may run open for demos. Staging and production must require either:

- `Authorization: Bearer <token>`; or
- `x-bive-api-key: <token>`.

The frontend exposes a token field and stores it only in browser `localStorage` when the user explicitly clicks the local save button.

## Request contract

`POST /api/v1/reports/from-transcript` accepts strict JSON:

```json
{
  "subject_scope": "public_statement_review",
  "segments": [
    {"speaker": "subject", "start": 0, "end": 4.1, "text": "..."}
  ]
}
```

Extra fields are rejected. Oversized payloads are rejected. Segment and text limits are exposed through `/api/v1/system/status`.

## Response contract

Report creation returns:

- `report_id`;
- `status`;
- `report` object;
- request id via `X-Request-ID` header.

Expected report fields used by the UI:

- `report.report_id`;
- `report.final_status`;
- `report.subject_scope`;
- `report.evidence_events[]`;
- `report.hypotheses[]`;
- `report.verification_questions[]`.

## Error contract

Errors return a stable JSON envelope:

```json
{
  "error": "validation_error",
  "details": ["..."],
  "request_id": "..."
}
```

## Frontend rendering contract

Dynamic report data is never rendered through raw HTML. The UI uses DOM creation and `textContent` for untrusted data.

## Verification

Run:

```bash
make frontend-quality
make api-smoke
pytest tests/test_api_operational_contract.py tests/test_frontend_contract.py -q
```

Acceptance:

- all consumed endpoints exist;
- system status renders gates and limits;
- report output renders summary, evidence, hypotheses, questions, JSON, and Markdown;
- forbidden dynamic HTML APIs are absent.
