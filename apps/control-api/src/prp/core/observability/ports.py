from __future__ import annotations

from typing import Protocol

from prp.core.observability.model import AuditEvent, Observation, UsageReceipt


class ObservationSink(Protocol):
    def record(self, observation: Observation) -> None: ...


class AuditSink(Protocol):
    def record(self, event: AuditEvent) -> None: ...


class UsageSink(Protocol):
    def record(self, receipt: UsageReceipt) -> None: ...
