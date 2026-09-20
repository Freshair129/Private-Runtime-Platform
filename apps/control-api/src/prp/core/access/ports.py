from __future__ import annotations

from datetime import datetime
from typing import Protocol

from prp.core.access.model import AccessKeyGrant, AuthContext


class KeyVerifier(Protocol):
    """Verifies a presented client key against a stored verifier.

    Implementations must be constant-time, must never persist, log or return the presented secret,
    and may delegate to a selected framework only when that framework meets PRP-FR-005
    (ADR-PRP-004; Xinference reveal-able keys do not).
    """

    def verify(self, presented_secret: str, *, now: datetime) -> AuthContext | None: ...


class GrantRepository(Protocol):
    def get_key_grant(self, key_id: str) -> AccessKeyGrant | None: ...
