from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from prp.core.access.model import AuthContext

MAX_GRANT_TTL = timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class Artifact:
    id: str
    organization_id: str
    owner_principal_id: str
    mime_type: str
    duration_seconds: float
    expires_at: datetime
    checksum_sha256: str | None = None
    tombstoned_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ArtifactGrant:
    """Revocable bearer capability, not a private channel (API-PRP §6)."""

    id: str
    artifact_id: str
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ErasureTombstone:
    artifact_id: str
    requested_at: datetime


def can_read(artifact: Artifact, context: AuthContext, *, now: datetime) -> bool:
    """Owner organization, not expired, not tombstoned; late output dies against a tombstone."""
    if artifact.tombstoned_at is not None or now >= artifact.expires_at:
        return False
    return artifact.organization_id == context.organization_id


def grant_expiry_allowed(
    artifact: Artifact, requested_expires_at: datetime, *, now: datetime
) -> bool:
    """Grant TTL is at most 24h and never outlives the artifact (API-PRP §6)."""
    if artifact.tombstoned_at is not None or requested_expires_at <= now:
        return False
    return requested_expires_at <= min(now + MAX_GRANT_TTL, artifact.expires_at)


def grant_is_live(grant: ArtifactGrant, artifact: Artifact, *, now: datetime) -> bool:
    if grant.artifact_id != artifact.id or artifact.tombstoned_at is not None:
        return False
    if grant.revoked_at is not None and grant.revoked_at <= now:
        return False
    return now < grant.expires_at and now < artifact.expires_at
