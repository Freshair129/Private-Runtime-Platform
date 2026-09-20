"""Admission Coordinator port and lease rules.

The port is implemented by a durable, race-tested primitive (transaction locks / CAS / unique
idempotency constraints) in ``prp.adapters.persistence``; never by a module-global dict or
asyncio.Lock (Coding-Standards §4). Lease rules encode ADR-PRP-005: a client deadline never
proves compute stopped, so it quarantines rather than releases.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Protocol

from prp.core.execution.model import ExecutionEvidence
from prp.core.scheduling.model import InvocationLease, LeaseState, Reservation, RoutePlan


class Admission(Protocol):
    def reserve(
        self,
        *,
        plan: RoutePlan,
        attempt_id: str,
        organization_id: str,
        principal_id: str,
        units: int,
        deadline_at: datetime,
    ) -> Reservation | None:
        """Atomically reserve the first candidate that still has capacity.

        Returns None when no candidate could be reserved before the deadline; the caller retries
        candidate selection within the remaining deadline instead of sending optimistically.
        """
        ...

    def release(self, lease_id: str) -> None: ...

    def quarantine(self, lease_id: str, *, reason: str) -> None: ...


def on_client_deadline(lease: InvocationLease) -> InvocationLease:
    """Timeout, cancel or lease expiry never equal compute stopped: quarantine, do not release."""
    if lease.state is LeaseState.RELEASED:
        return lease
    return replace(lease, state=LeaseState.QUARANTINED)


def on_termination_evidence(lease: InvocationLease, evidence: ExecutionEvidence) -> InvocationLease:
    """Only FINISHED evidence releases a lease; RUNNING keeps it, UNKNOWN keeps it quarantined."""
    if evidence is ExecutionEvidence.FINISHED:
        return replace(lease, state=LeaseState.RELEASED)
    if evidence is ExecutionEvidence.UNKNOWN and lease.state is LeaseState.HELD:
        return replace(lease, state=LeaseState.QUARANTINED)
    return lease
