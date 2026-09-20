from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum

from prp_voice.contract.models import Readiness, ReadinessValue


class Phase(StrEnum):
    LOADING = "LOADING"
    READY = "READY"
    DRAINING = "DRAINING"
    STOPPED = "STOPPED"


@dataclass(frozen=True, slots=True)
class Identity:
    runtime_uid: str
    physical_resource_id: str
    profile_hash: str
    profile_epoch: int
    manager_uid: str | None = None

    @property
    def is_complete(self) -> bool:
        return bool(self.runtime_uid and self.physical_resource_id and self.profile_hash)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Lifecycle:
    def __init__(self, identity: Identity, *, clock: Callable[[], datetime] = _utcnow) -> None:
        self._identity = identity
        self._phase = Phase.LOADING
        self._observation_failed = False
        self._clock = clock

    @property
    def identity(self) -> Identity:
        return self._identity

    @property
    def phase(self) -> Phase:
        return self._phase

    def mark_ready(self) -> None:
        if not self._identity.is_complete:
            raise ValueError("cannot become READY without a complete operator-assigned identity")
        if self._phase is Phase.STOPPED:
            raise ValueError("a STOPPED worker cannot become READY; restart and requalify")
        self._phase = Phase.READY
        self._observation_failed = False

    def drain(self) -> None:
        if self._phase is not Phase.STOPPED:
            self._phase = Phase.DRAINING

    def stop(self) -> None:
        self._phase = Phase.STOPPED

    def mark_observation_failed(self) -> None:
        """The engine could not be observed; readiness becomes UNKNOWN, never READY by default."""
        self._observation_failed = True

    def bump_epoch(self, new_profile_hash: str) -> Identity:
        """A profile change fences every invocation reserved against the old epoch."""
        self._identity = replace(
            self._identity,
            profile_hash=new_profile_hash,
            profile_epoch=self._identity.profile_epoch + 1,
        )
        self._phase = Phase.LOADING
        return self._identity

    def readiness(self, requested_epoch: int) -> Readiness:
        state: ReadinessValue
        if self._observation_failed:
            state = "UNKNOWN"
        elif self._phase is Phase.READY and requested_epoch == self._identity.profile_epoch:
            state = "READY"
        else:
            state = "NOT_READY"
        return Readiness(
            state=state,
            profile_epoch=self._identity.profile_epoch,
            observed_at=self._clock(),
        )
