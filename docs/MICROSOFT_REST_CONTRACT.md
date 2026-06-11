# Microsoft REST Contract

BIVE now exposes a Microsoft/Azure-style API contract for versioning, correlation and error handling.

Required API behavior:

- every `/api/v1/*` operation requires `api-version=2026-06-11`;
- missing version returns `MissingApiVersionParameter`;
- unsupported version returns `UnsupportedApiVersion`;
- responses include `x-ms-request-id`;
- `x-ms-client-request-id` is echoed when supplied;
- error responses use:

```json
{
  "error": {
    "code": "ValidationError",
    "message": "Request validation failed.",
    "details": [],
    "innererror": {
      "requestId": "...",
      "clientRequestId": "..."
    }
  }
}
```

Release gate:

```bash
make microsoft-rest
```
