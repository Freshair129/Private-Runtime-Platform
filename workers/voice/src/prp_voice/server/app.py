"""Worker application factory.

Routes are bound to the generated worker contract models (ADR-PRP-013): FastAPI validates every
JSON request against contracts/openapi/prp-worker.yaml before a handler runs. M3 semantics stay:
no engine is configured, so describe and invoke fail closed with RUNTIME_UNAVAILABLE, cancel
reports UNSUPPORTED and execution evidence reports 501 UNSUPPORTED. These are the honest answers of
an adapter without an engine (ADR-PRP-005), not placeholders for success.
"""

import hmac
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from prp_voice import __version__
from prp_voice.contract.models import (
    CancelRequest,
    CancelResult,
    Describe,
    ErrorCode,
    ExecutionEvidence,
    InvocationRequest,
    InvocationResult,
    Readiness,
)
from prp_voice.lifecycle import Lifecycle

HEADER = "X-Request-ID"
HTTP_STATUS: dict[str, int] = {
    "INVALID_REQUEST": 400,
    "UNSUPPORTED_PARAMETER": 400,
    "PAYLOAD_TOO_LARGE": 400,
    "EPOCH_MISMATCH": 409,
    "FENCE_REJECTED": 409,
    "NOT_FOUND": 404,
    "UNSUPPORTED": 501,
    "CONTEXT_LIMIT": 422,
    "NO_SPEECH": 422,
    "AUDIO_UNINTELLIGIBLE": 422,
    "RUNTIME_UNAVAILABLE": 503,
    "DEADLINE_EXCEEDED": 504,
}
Epoch = Annotated[int, Query(ge=0)]


class WorkerError(Exception):
    def __init__(self, code: ErrorCode, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.code: ErrorCode = code
        self.message = message
        self.status = status if status is not None else HTTP_STATUS[code]


def envelope(error: WorkerError, request_id: str) -> dict[str, object]:
    return {
        "error": {"code": error.code, "type": "worker", "message": error.message, "param": None},
        "request_id": request_id,
        "safe_to_retry": False,
    }


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[HEADER] = request_id
        return response


def _request_id(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) else str(uuid.uuid4())


def _respond(request: Request, error: WorkerError) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=error.status, content=envelope(error, request_id), headers={HEADER: request_id}
    )


class ServiceCredential:
    """Constant-time bearer check. No configured token means fail closed."""

    def __init__(self, expected: str | None) -> None:
        self._expected = expected

    def __call__(self, request: Request) -> None:
        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer ") or not header[7:].strip():
            raise WorkerError("INVALID_REQUEST", "missing service credential", status=401)
        if self._expected is None:
            raise WorkerError("RUNTIME_UNAVAILABLE", "no service credential configured on worker")
        if not hmac.compare_digest(header[7:].strip().encode(), self._expected.encode()):
            raise WorkerError("INVALID_REQUEST", "service credential rejected", status=401)


def create_app(lifecycle: Lifecycle, *, service_token: str | None) -> FastAPI:
    app = FastAPI(
        title="PRP - Worker Adapter Contract",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        dependencies=[Depends(ServiceCredential(service_token))],
    )
    app.add_middleware(RequestIdMiddleware)

    async def handle_worker_error(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, WorkerError):
            return _respond(request, exc)
        raise exc

    async def handle_validation(request: Request, exc: Exception) -> JSONResponse:
        return _respond(request, WorkerError("INVALID_REQUEST", "request rejected by contract"))

    async def handle_http(request: Request, exc: Exception) -> JSONResponse:
        return _respond(request, WorkerError("NOT_FOUND", "unknown route"))

    app.add_exception_handler(WorkerError, handle_worker_error)
    app.add_exception_handler(RequestValidationError, handle_validation)
    app.add_exception_handler(StarletteHTTPException, handle_http)

    @app.get("/prp/worker/v1/describe", operation_id="describeRuntime", response_model=Describe)
    def describe() -> Describe:
        raise WorkerError("RUNTIME_UNAVAILABLE", "no engine configured; nothing to describe")

    @app.get("/prp/worker/v1/readiness", operation_id="getReadiness", response_model=Readiness)
    def readiness(profile_epoch: Epoch) -> Readiness:
        return lifecycle.readiness(profile_epoch)

    @app.post("/prp/worker/v1/invocations", operation_id="invoke", response_model=InvocationResult)
    def invoke(body: InvocationRequest) -> InvocationResult:
        raise WorkerError("RUNTIME_UNAVAILABLE", "no engine configured; invocation refused")

    @app.get(
        "/prp/worker/v1/invocations/{attempt_id}",
        operation_id="getExecutionEvidence",
        response_model=ExecutionEvidence,
    )
    def execution_evidence(attempt_id: UUID, runtime_epoch: Epoch) -> ExecutionEvidence:
        raise WorkerError("UNSUPPORTED", "this adapter cannot report termination evidence yet")

    @app.post(
        "/prp/worker/v1/invocations/{attempt_id}/cancel",
        operation_id="cancelAttempt",
        response_model=CancelResult,
    )
    def cancel(attempt_id: UUID, body: CancelRequest) -> CancelResult:
        return CancelResult(
            attempt_id=attempt_id, disposition="UNSUPPORTED", observed_at=datetime.now(UTC)
        )

    return app
