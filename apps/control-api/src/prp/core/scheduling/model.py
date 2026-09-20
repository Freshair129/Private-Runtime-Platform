from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class LeaseState(StrEnum):
    HELD = "HELD"
    RELEASED = "RELEASED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class Candidate:
    node_id: str
    pool_label: str
    profile_epoch: int


@dataclass(frozen=True, slots=True)
class RoutePlan:
    ranked: tuple[Candidate, ...]
    reason: str

    @property
    def is_empty(self) -> bool:
        return not self.ranked


@dataclass(frozen=True, slots=True)
class QuotaReservation:
    id: str
    organization_id: str
    principal_id: str
    units: int
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ModelResidency:
    """Calibrated baseline memory held while a model stays loaded (ARCH-PRP §5)."""

    node_id: str
    profile_epoch: int
    baseline_memory_bytes: int | None


@dataclass(frozen=True, slots=True)
class InvocationLease:
    id: str
    attempt_id: str
    node_id: str
    profile_epoch: int
    slots: int
    token_budget: int | None
    expires_at: datetime
    state: LeaseState


@dataclass(frozen=True, slots=True)
class Reservation:
    quota: QuotaReservation
    lease: InvocationLease
