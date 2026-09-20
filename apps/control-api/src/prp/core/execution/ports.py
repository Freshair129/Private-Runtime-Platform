from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from prp.core.execution.model import (
    Attempt,
    CancelDisposition,
    ExecutionEvidence,
    OutboxRecord,
    ResultEnvelope,
)


class OutboxStore(Protocol):
    """Durable dispatch outbox; claims and transitions are atomic across dispatcher processes."""

    def claim_next(self, *, dispatcher_id: str) -> OutboxRecord | None: ...

    def mark_dispatching(self, record: OutboxRecord) -> None: ...

    def mark_sent(self, record: OutboxRecord) -> None: ...


class RuntimeInvoker(Protocol):
    """Worker adapter port; mirrors contracts/openapi/prp-worker.yaml.

    Adapters normalize vendor errors to stable codes and never pass vendor objects or tracebacks
    through (Coding-Standards §5). Cancelling a coroutine or future is not hard termination.
    """

    def invoke(self, attempt: Attempt, payload: Mapping[str, object]) -> ResultEnvelope: ...

    def cancel(self, attempt: Attempt) -> CancelDisposition: ...

    def execution_evidence(self, attempt: Attempt) -> ExecutionEvidence: ...
