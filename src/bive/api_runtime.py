from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any, Literal, cast
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .aos import kernel_status
from .api_models import (
    CapabilityResponse,
    DesignContractResponse,
    GateStatus,
    RuntimeLimitsResponse,
    StorageStatsResponse,
    SystemStatusResponse,
    TranscriptAnalyzeRequest,
)
from .cognitive_control import cognitive_control_status
from .neurocognitive import neurocognitive_protocol_status
from .observability import log_event
from .pipeline import analyze_transcript_payload
from .product import product_readiness_status
from .report import render_markdown
from .science import load_science_registry, science_registry_summary
from .settings import get_settings
from .storage import ReportStore

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
WEB_ROOT = PACKAGE_ROOT / "web"
STATIC_ROOT = WEB_ROOT / "static"
settings = get_settings()
store = ReportStore(settings.storage_path)
REQUEST_COUNT = 0
REQUEST_ERROR_COUNT = 0
REQUEST_LATENCY_SECONDS_SUM = 0.0

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'",
}

RELEASE_GATES: tuple[GateStatus, ...] = (
    GateStatus(
        name="repo-clean", command="python scripts/check_repo_clean.py", last_observed="pass"
    ),
    GateStatus(
        name="metadata", command="python scripts/validate_metadata.py", last_observed="pass"
    ),
    GateStatus(name="lint", command="ruff check src tests scripts", last_observed="pass"),
    GateStatus(name="typecheck", command="mypy src", last_observed="pass"),
    GateStatus(
        name="coverage", command="pytest --cov=bive --cov-fail-under=80", last_observed="pass"
    ),
    GateStatus(
        name="schema",
        command="python scripts/validate_schemas.py --strict --instances",
        last_observed="pass",
    ),
    GateStatus(
        name="openapi",
        command="python scripts/export_openapi.py --output docs/openapi.json --check",
        last_observed="pass",
    ),
    GateStatus(name="wheel-smoke", command="python scripts/wheel_smoke.py", last_observed="pass"),
    GateStatus(
        name="security-static",
        command="bandit -q -r src scripts -c pyproject.toml -ll",
        last_observed="pass",
    ),
    GateStatus(
        name="science-registry",
        command="python scripts/validate_science_registry.py",
        last_observed="pass",
    ),
    GateStatus(
        name="dynamic-probe",
        command="python scripts/dynamic_environment_probe.py",
        last_observed="pass",
    ),
    GateStatus(
        name="threat-model",
        command="python scripts/validate_threat_model.py",
        last_observed="pass",
    ),
    GateStatus(
        name="microsoft-rest",
        command="python scripts/validate_microsoft_rest_contract.py",
        last_observed="pass",
    ),
    GateStatus(
        name="operational-excellence",
        command="python scripts/validate_operational_excellence.py",
        last_observed="pass",
    ),
    GateStatus(
        name="aos-kernel", command="python scripts/validate_aos_kernel.py", last_observed="pass"
    ),
    GateStatus(name="product-readiness", command="python scripts/validate_product_operating_model.py", last_observed="pass"),
    GateStatus(name="dependency-audit", command="pip-audit --format=json", last_observed="unknown"),
    GateStatus(
        name="docker-runtime", command="docker build/run + /readyz", last_observed="unknown"
    ),
)

app = FastAPI(
    title="BIVE API",
    version=settings.version,
    description="Behavioral Integrity Verification Engine API: evidence-first behavioral verification, not automated accusation.",
)
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


def _request_id(request: Request) -> str:
    return request.headers.get("x-ms-request-id") or request.headers.get("x-request-id") or str(uuid4())


def _client_request_id(request: Request) -> str | None:
    value = request.headers.get("x-ms-client-request-id")
    return str(value) if value is not None else None


def _apply_security_headers(response: Response) -> Response:
    response.headers.setdefault("X-BIVE-Version", settings.version)
    response.headers.setdefault("X-BIVE-Api-Version", settings.api_version)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


def _record_metrics(status_code: int, elapsed_seconds: float) -> None:
    global REQUEST_COUNT, REQUEST_ERROR_COUNT, REQUEST_LATENCY_SECONDS_SUM
    REQUEST_COUNT += 1
    if status_code >= 400:
        REQUEST_ERROR_COUNT += 1
    REQUEST_LATENCY_SECONDS_SUM += elapsed_seconds


def _error_response(
    status_code: int,
    code: str,
    details: list[str],
    request_id: str,
    client_request_id: str | None = None,
    message: str | None = None,
) -> JSONResponse:
    headers = {"X-Request-ID": request_id, "x-ms-request-id": request_id}
    if client_request_id:
        headers["x-ms-client-request-id"] = client_request_id
    response = JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "error": {
                "code": code,
                "message": message or code,
                "details": details,
                "innererror": {
                    "requestId": request_id,
                    "clientRequestId": client_request_id,
                },
            }
        },
    )
    return cast(JSONResponse, _apply_security_headers(response))


@app.middleware("http")
async def enforce_runtime_boundary(request: Request, call_next: Any) -> Response:
    started = perf_counter()
    request_id = _request_id(request)
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            length = int(content_length)
        except ValueError:
            early_response = _error_response(400, "InvalidContentLength", [], request_id, _client_request_id(request), "Content-Length must be an integer.")
            _record_metrics(early_response.status_code, perf_counter() - started)
            return early_response
        if length > settings.max_upload_bytes:
            early_response = _error_response(413, "PayloadTooLarge", [], request_id, _client_request_id(request), "Payload exceeds configured upload limit.")
            _record_metrics(early_response.status_code, perf_counter() - started)
            return early_response
    response = cast(Response, await call_next(request))
    elapsed = perf_counter() - started
    _record_metrics(response.status_code, elapsed)
    log_event(
        "api_request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        elapsed_seconds=round(elapsed, 6),
    )
    response.headers.setdefault("X-Request-ID", request_id)
    response.headers.setdefault("x-ms-request-id", request_id)
    client_request_id = _client_request_id(request)
    if client_request_id:
        response.headers.setdefault("x-ms-client-request-id", client_request_id)
    return _apply_security_headers(response)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = _request_id(request)
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return _error_response(exc.status_code, detail, [], request_id, _client_request_id(request))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = _request_id(request)
    details = [str(error.get("msg", "validation_error")) for error in exc.errors()]
    return _error_response(422, "ValidationError", details, request_id, _client_request_id(request), "Request validation failed.")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return _error_response(400, "InvalidInput", [str(exc)], _request_id(request), _client_request_id(request))




def require_api_version(api_version: str | None = Query(default=None, alias="api-version")) -> None:
    if api_version is None:
        raise HTTPException(status_code=400, detail="MissingApiVersionParameter")
    if api_version != settings.api_version:
        raise HTTPException(status_code=400, detail="UnsupportedApiVersion")

def require_api_auth(
    authorization: str | None = Header(default=None),
    x_bive_api_key: str | None = Header(default=None),
) -> None:
    if not settings.auth_required:
        return
    if not settings.api_token:
        raise HTTPException(status_code=503, detail="api_token_not_configured")
    bearer = f"Bearer {settings.api_token}"
    if authorization == bearer or x_bive_api_key == settings.api_token:
        return
    raise HTTPException(status_code=401, detail="authentication_required")


def validate_runtime_payload(payload: TranscriptAnalyzeRequest) -> None:
    if len(payload.segments) > settings.max_segments:
        raise HTTPException(status_code=422, detail="too_many_segments")
    for index, segment in enumerate(payload.segments):
        if len(segment.text) > settings.max_text_chars:
            raise HTTPException(status_code=422, detail=f"segment_{index}_text_too_large")


def _limits() -> RuntimeLimitsResponse:
    return RuntimeLimitsResponse(
        max_upload_bytes=settings.max_upload_bytes,
        max_segments=settings.max_segments,
        max_text_chars=settings.max_text_chars,
        auth_required=settings.auth_required,
        allow_person_level_verdicts=settings.allow_person_level_verdicts,
    )


def _latest_gate_statuses() -> tuple[GateStatus, ...]:
    gates_path = REPO_ROOT / "artifacts" / "verification" / "gates.json"
    if not gates_path.exists():
        return RELEASE_GATES
    try:
        payload = __import__("json").loads(gates_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return RELEASE_GATES
    observed = []
    for item in payload.get("gates", []):
        if not isinstance(item, dict):
            continue
        command = item.get("command", [])
        name = " ".join(str(part) for part in command) or "unknown"
        status = str(item.get("result", "unknown"))
        if status not in {"pass", "fail", "unknown"}:
            status = "unknown"
        observed_status = cast(Literal["pass", "fail", "unknown"], status)
        observed.append(GateStatus(name=name, command=name, last_observed=observed_status))
    return tuple(observed) or RELEASE_GATES


def _storage_stats() -> StorageStatsResponse:
    stats = store.stats()
    return StorageStatsResponse(
        report_count=stats["report_count"],
        audit_event_count=stats["audit_event_count"],
        schema_version=stats["schema_version"],
        storage_path_configured=bool(settings.storage_path),
    )


@app.get("/", response_class=HTMLResponse)
def ui() -> str:
    return (WEB_ROOT / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "allow_person_level_verdicts": settings.allow_person_level_verdicts,
    }


@app.get("/livez")
def livez() -> dict[str, str]:
    return {"status": "live"}


@app.get("/readyz")
def readyz() -> JSONResponse:
    errors = list(settings.config_errors)
    try:
        store.healthcheck()
    except OSError as exc:
        errors.append(str(exc))
    if errors:
        return JSONResponse(status_code=503, content={"status": "not_ready", "errors": errors})
    return JSONResponse(status_code=200, content={"status": "ready"})


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    lines = [
        "# HELP bive_requests_total Total HTTP requests observed by BIVE middleware.",
        "# TYPE bive_requests_total counter",
        f"bive_requests_total {REQUEST_COUNT}",
        "# HELP bive_request_errors_total HTTP 5xx responses observed by BIVE middleware.",
        "# TYPE bive_request_errors_total counter",
        f"bive_request_errors_total {REQUEST_ERROR_COUNT}",
        "# HELP bive_request_latency_seconds_sum Sum of request latencies observed by BIVE middleware.",
        "# TYPE bive_request_latency_seconds_sum counter",
        f"bive_request_latency_seconds_sum {REQUEST_LATENCY_SECONDS_SUM:.6f}",
    ]
    return "\n".join(lines) + "\n"


@app.get("/api/v1/capabilities", response_model=CapabilityResponse, dependencies=[Depends(require_api_version)])
def capabilities() -> CapabilityResponse:
    return CapabilityResponse(
        modalities=["text", "audio", "vision", "context"],
        invariants=[
            "No automatic person-level liar label.",
            "No single cue may decide a hypothesis.",
            "Every elevated hypothesis must include counter-evidence or missing evidence.",
            "Human review required for real-world decisions.",
        ],
        outputs=[
            "verification_report",
            "evidence_events",
            "hypotheses",
            "verification_questions",
            "markdown_report",
        ],
        production_gates=[gate.name for gate in RELEASE_GATES],
        optional_adapters=["whisper", "openface", "opensmile", "pyannote", "mediapipe"],
    )


@app.get("/api/v1/system/science-registry", dependencies=[Depends(require_api_version)])
def science_registry() -> dict[str, Any]:
    return science_registry_summary()


@app.get("/api/v1/system/science-registry/full", dependencies=[Depends(require_api_version)])
def full_science_registry() -> dict[str, Any]:
    return load_science_registry()


@app.get("/api/v1/system/status", response_model=SystemStatusResponse, dependencies=[Depends(require_api_version)])
def system_status() -> SystemStatusResponse:
    errors = list(settings.config_errors)
    try:
        store.healthcheck()
    except OSError as exc:
        errors.append(str(exc))
    return SystemStatusResponse(
        service=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        readiness="not_ready" if errors else "ready",
        config_errors=errors,
        limits=_limits(),
        storage=_storage_stats(),
        gates=list(_latest_gate_statuses()),
    )


@app.get("/api/v1/system/design-contract", response_model=DesignContractResponse, dependencies=[Depends(require_api_version)])
def design_contract() -> DesignContractResponse:
    return DesignContractResponse(
        product_layer="single-page operational console over a strict FastAPI/OpenAPI backend",
        interaction_model="load sample, edit transcript JSON, run analysis, inspect evidence, retrieve markdown",
        accessibility_target="WCAG 2.2 AA-oriented semantic HTML, labels, focus states, aria-live status, keyboard-operable controls",
        security_model="local mode open for demos; staging/production requires bearer token or x-bive-api-key",
        operational_model="health, readiness, metrics, request-id, release gates, manifest, dynamic probes, science registry validation and wheel smoke evidence",
        evidence_policy="reviewable evidence graph only; no automatic person-level lie, guilt or legal verdict",
    )


@app.get("/api/v1/system/aos-kernel", dependencies=[Depends(require_api_version)])
def aos_kernel() -> dict[str, Any]:
    return kernel_status()


@app.get("/api/v1/system/cognitive-control-plane", dependencies=[Depends(require_api_version)])
def cognitive_control_plane() -> dict[str, Any]:
    return cognitive_control_status()




@app.get("/api/v1/system/neurocognitive-protocol", dependencies=[Depends(require_api_version)])
def neurocognitive_protocol() -> dict[str, Any]:
    return neurocognitive_protocol_status()


@app.get("/api/v1/system/product-readiness", dependencies=[Depends(require_api_version)])
def product_readiness() -> dict[str, Any]:
    return product_readiness_status()

@app.get("/api/v1/system/interface-contract", dependencies=[Depends(require_api_version)])
def interface_contract() -> dict[str, Any]:
    return {
        "visual_language": {
            "mode": "dark operational console",
            "tokens": ["bg", "panel", "gold", "good", "bad", "busy", "muted"],
            "layout": "responsive evidence-first dashboard with semantic sections",
        },
        "frontend_controls": [
            "safe DOM rendering for dynamic report fields",
            "keyboard-operable controls",
            "aria-live status feedback",
            "local token entry for staged deployments",
            "JSON and Markdown export",
        ],
        "knowledge_controls": [
            "bounded scientific reference registry",
            "discipline-to-claim-boundary mapping",
            "explicit no automatic lie/guilt/intent/diagnosis boundary",
            "dynamic environment probe registry",
        ],
        "backend_controls": [
            "strict request schema",
            "request-id propagation",
            "readiness and metrics endpoints",
            "security headers",
            "production authentication boundary",
        ],
    }


@app.post("/api/v1/reports/from-transcript", dependencies=[Depends(require_api_version), Depends(require_api_auth)])
def create_report(payload: TranscriptAnalyzeRequest) -> dict[str, Any]:
    validate_runtime_payload(payload)
    report = analyze_transcript_payload(payload.model_dump(), subject_scope=payload.subject_scope)
    store.save(report)
    return {
        "report_id": report.report_id,
        "status": report.final_status.value,
        "report": report.to_dict(),
    }


@app.get("/api/v1/reports", dependencies=[Depends(require_api_version), Depends(require_api_auth)])
def list_reports(limit: int = 20) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), 100)
    return {"reports": [x.to_dict() for x in store.list(limit=safe_limit)]}


@app.get("/api/v1/reports/{report_id}", dependencies=[Depends(require_api_version), Depends(require_api_auth)])
def get_report(report_id: str) -> dict[str, Any]:
    report = store.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report_not_found")
    return {"report": report.to_dict()}


@app.get(
    "/api/v1/reports/{report_id}/markdown",
    response_class=PlainTextResponse,
    dependencies=[Depends(require_api_version), Depends(require_api_auth)],
)
def get_report_markdown(report_id: str) -> str:
    report = store.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report_not_found")
    return render_markdown(report)


def main() -> int:
    from .api import main as api_main

    return api_main()


if __name__ == "__main__":
    raise SystemExit(main())
