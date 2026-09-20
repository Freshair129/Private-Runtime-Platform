"""Every error leaves the API as the contract Error envelope with X-Request-ID (API-PRP §2)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from prp.api.request_id import HEADER, request_id_of
from prp.platform.errors import ErrorCode, PrpError


def respond(request: Request, error: PrpError) -> JSONResponse:
    request_id = request_id_of(request)
    return JSONResponse(
        status_code=error.http_status,
        content=error.envelope(request_id),
        headers={HEADER: request_id},
    )


async def handle_prp_error(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, PrpError):
        return respond(request, exc)
    raise exc


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    return respond(
        request,
        PrpError(
            ErrorCode.INVALID_REQUEST,
            "request does not match the published contract",
            safe_to_retry=True,
        ),
    )


async def handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    status = exc.status_code if isinstance(exc, StarletteHTTPException) else 404
    if status in (404, 405):
        error = PrpError(ErrorCode.NOT_FOUND, "missing or unauthorized object", safe_to_retry=True)
    else:
        error = PrpError(
            ErrorCode.STATE_STORE_UNAVAILABLE, "control plane failed closed", safe_to_retry=False
        )
    return respond(request, error)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PrpError, handle_prp_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
