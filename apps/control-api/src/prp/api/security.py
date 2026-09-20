"""Client-key authentication facade.

The API derives organization and principal from the verified key only; supplied IDs never grant
access (API-PRP §2). Without a configured verifier the API fails closed (ARCH-PRP §10) instead of
pretending a key check happened.
"""

from fastapi import Request

from prp.core.access.model import AuthContext
from prp.core.access.ports import KeyVerifier
from prp.platform.clock import Clock
from prp.platform.errors import ErrorCode, PrpError


def bearer_secret(request: Request) -> str:
    header = request.headers.get("authorization")
    if header is None or not header.lower().startswith("bearer "):
        raise PrpError(ErrorCode.INVALID_KEY, "missing or malformed bearer credential")
    secret = header[7:].strip()
    if not secret:
        raise PrpError(ErrorCode.INVALID_KEY, "missing or malformed bearer credential")
    return secret


class ClientKeyAuth:
    def __init__(self, verifier: KeyVerifier | None, clock: Clock) -> None:
        self._verifier = verifier
        self._clock = clock

    def __call__(self, request: Request) -> AuthContext:
        secret = bearer_secret(request)
        if self._verifier is None:
            raise PrpError(
                ErrorCode.STATE_STORE_UNAVAILABLE,
                "no key verifier configured; refusing to authenticate",
                safe_to_retry=False,
            )
        context = self._verifier.verify(secret, now=self._clock.now())
        if context is None:
            raise PrpError(ErrorCode.INVALID_KEY, "credential rejected")
        return context
