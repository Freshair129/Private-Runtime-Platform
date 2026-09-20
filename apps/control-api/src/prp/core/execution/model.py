from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Kind(StrEnum):
    CHAT = "chat"
    ASR = "asr"
    TTS = "tts"


class Outcome(StrEnum):
    """Logical outcome seen by the client (client contract Job.outcome)."""

    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class ExecutionStatus(StrEnum):
    """Execution dimension, independent of Outcome (client contract Job.execution_status)."""

    QUEUED = "QUEUED"
    RESERVED = "RESERVED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    UNKNOWN = "UNKNOWN"
    FINISHED = "FINISHED"


class ExecutionEvidence(StrEnum):
    """Worker-reported evidence (contracts/openapi/prp-worker.yaml ExecutionEvidence)."""

    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    UNKNOWN = "UNKNOWN"


class CancelDisposition(StrEnum):
    ACK = "ACK"
    UNSUPPORTED = "UNSUPPORTED"
    ALREADY_FINISHED = "ALREADY_FINISHED"


class UsageProvenance(StrEnum):
    ACTUAL = "actual"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class OutboxState(StrEnum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    DISPATCHING = "DISPATCHING"
    SENT = "SENT"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class Invocation:
    id: str
    organization_id: str
    principal_id: str
    kind: Kind
    deadline_at: datetime
    idempotency_key: str | None


@dataclass(frozen=True, slots=True)
class Attempt:
    id: str
    invocation_id: str
    node_id: str
    profile_epoch: int
    fence_token: str
    execution: ExecutionStatus
    dispatched_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Job:
    id: str
    invocation_id: str
    kind: Kind
    outcome: Outcome
    execution: ExecutionStatus
    cancellation_requested: bool
    created_at: datetime
    deadline_at: datetime
    settled_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    attempt_id: str
    node_id: str
    profile_epoch: int
    state: OutboxState
    claimed_by: str | None = None


@dataclass(frozen=True, slots=True)
class ResultEnvelope:
    """Identity fields every worker result must echo (ARCH-PRP §6)."""

    invocation_id: str
    attempt_id: str
    runtime_uid: str
    physical_resource_id: str
    profile_epoch: int
    fence_token: str
