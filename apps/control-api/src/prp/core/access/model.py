from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PrincipalKind(StrEnum):
    HUMAN = "human"
    APPLICATION = "application"


class Scope(StrEnum):
    CHAT = "chat"
    ASR = "asr"
    TTS = "tts"
    JOBS = "jobs"
    ARTIFACTS = "artifacts"


@dataclass(frozen=True, slots=True)
class Organization:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Principal:
    id: str
    organization_id: str
    kind: PrincipalKind


@dataclass(frozen=True, slots=True)
class AccessKeyGrant:
    """What a key is allowed to do. The secret is never part of this object (PRP-FR-005)."""

    key_id: str
    key_prefix: str
    principal_id: str
    organization_id: str
    scopes: frozenset[Scope]
    pool_ids: frozenset[str]
    expires_at: datetime | None
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Trusted identity derived from a verified key. Supplied org/team IDs never grant access."""

    organization_id: str
    principal_id: str
    key_id: str
    scopes: frozenset[Scope]


def is_active(grant: AccessKeyGrant, *, now: datetime) -> bool:
    if grant.revoked_at is not None and grant.revoked_at <= now:
        return False
    return grant.expires_at is None or now < grant.expires_at


def has_scope(context: AuthContext, scope: Scope) -> bool:
    return scope in context.scopes
