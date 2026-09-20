from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from prp.core.execution.model import UsageProvenance


class ReadinessState(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Observation:
    """Normalized readiness observation of one node; stale observations are not evidence."""

    node_id: str
    profile_epoch: int
    state: ReadinessState
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class UsageReceipt:
    attempt_id: str
    invocation_id: str
    units: int
    provenance: UsageProvenance
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Metadata-only audit fact. There is deliberately no free-form payload field."""

    id: str
    occurred_at: datetime
    request_id: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str
    actor_principal_id: str | None = None
