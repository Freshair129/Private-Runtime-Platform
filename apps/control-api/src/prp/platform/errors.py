"""Stable error codes and the public error envelope (API-PRP §2).

Codes are the contract. Messages are sanitized and never carry upstream bodies, stack traces or
secrets (Coding-Standards §5). `safe_to_retry` is False whenever work may already have been
dispatched (ADR-PRP-005).
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_PARAMETER = "UNSUPPORTED_PARAMETER"
    INVALID_KEY = "INVALID_KEY"
    EXPIRED_KEY = "EXPIRED_KEY"
    SCOPE_DENIED = "SCOPE_DENIED"
    POLICY_DENIED = "POLICY_DENIED"
    NOT_FOUND = "NOT_FOUND"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    AUDIO_TOO_LARGE = "AUDIO_TOO_LARGE"
    AUDIO_FORMAT_UNSUPPORTED = "AUDIO_FORMAT_UNSUPPORTED"
    CONTEXT_LIMIT = "CONTEXT_LIMIT"
    NO_SPEECH = "NO_SPEECH"
    AUDIO_UNINTELLIGIBLE = "AUDIO_UNINTELLIGIBLE"
    ASYNC_REQUIRED = "ASYNC_REQUIRED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    QUEUE_FULL = "QUEUE_FULL"
    NO_ELIGIBLE_NODE = "NO_ELIGIBLE_NODE"
    STATE_STORE_UNAVAILABLE = "STATE_STORE_UNAVAILABLE"
    DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"


HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.UNSUPPORTED_PARAMETER: 400,
    ErrorCode.INVALID_KEY: 401,
    ErrorCode.EXPIRED_KEY: 401,
    ErrorCode.SCOPE_DENIED: 403,
    ErrorCode.POLICY_DENIED: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.IDEMPOTENCY_CONFLICT: 409,
    ErrorCode.VERSION_CONFLICT: 409,
    ErrorCode.AUDIO_TOO_LARGE: 413,
    ErrorCode.AUDIO_FORMAT_UNSUPPORTED: 415,
    ErrorCode.CONTEXT_LIMIT: 422,
    ErrorCode.NO_SPEECH: 422,
    ErrorCode.AUDIO_UNINTELLIGIBLE: 422,
    ErrorCode.ASYNC_REQUIRED: 422,
    ErrorCode.QUOTA_EXCEEDED: 429,
    ErrorCode.QUEUE_FULL: 429,
    ErrorCode.NO_ELIGIBLE_NODE: 503,
    ErrorCode.STATE_STORE_UNAVAILABLE: 503,
    ErrorCode.DEADLINE_EXCEEDED: 504,
}

# `error.type` category per HTTP class. Category names are a draft to freeze at WP03.
ERROR_TYPE: dict[int, str] = {
    400: "invalid_request",
    401: "authentication",
    403: "authorization",
    404: "not_found",
    409: "conflict",
    413: "limit",
    415: "invalid_request",
    422: "unprocessable",
    429: "limit",
    503: "unavailable",
    504: "timeout",
}


class PrpError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        param: str | None = None,
        safe_to_retry: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.param = param
        self.safe_to_retry = safe_to_retry

    @property
    def http_status(self) -> int:
        return HTTP_STATUS[self.code]

    def envelope(self, request_id: str) -> dict[str, object]:
        return {
            "error": {
                "code": self.code.value,
                "type": ERROR_TYPE[self.http_status],
                "message": self.message,
                "param": self.param,
            },
            "request_id": request_id,
            "safe_to_retry": self.safe_to_retry,
        }
