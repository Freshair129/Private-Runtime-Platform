from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ErrorCode = Literal[
    "INVALID_REQUEST",
    "UNSUPPORTED_PARAMETER",
    "PAYLOAD_TOO_LARGE",
    "EPOCH_MISMATCH",
    "FENCE_REJECTED",
    "NOT_FOUND",
    "UNSUPPORTED",
    "CONTEXT_LIMIT",
    "NO_SPEECH",
    "AUDIO_UNINTELLIGIBLE",
    "RUNTIME_UNAVAILABLE",
    "DEADLINE_EXCEEDED",
]
ReadinessValue = Literal["READY", "NOT_READY", "UNKNOWN"]
EvidenceValue = Literal["RUNNING", "FINISHED", "UNKNOWN"]
CancelValue = Literal["ACK", "UNSUPPORTED", "ALREADY_FINISHED"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ErrorBody(StrictModel):
    code: ErrorCode
    type: str
    message: str
    param: str | None = None


class Error(StrictModel):
    error: ErrorBody
    request_id: str
    safe_to_retry: bool


class RuntimeIdentity(StrictModel):
    manager_uid: str | None = None
    runtime_uid: str
    physical_resource_id: str
    profile_hash: str
    profile_epoch: int = Field(ge=0)
    engine: str
    adapter_version: str
    evidence_revision: str | None = None


class Limits(StrictModel):
    max_context_tokens: int | None = Field(default=None, ge=1)
    max_audio_seconds: float | None = Field(default=None, gt=0)
    max_input_bytes: int | None = Field(default=None, ge=1)
    max_tts_codepoints: int | None = Field(default=None, ge=1)
    max_concurrent_invocations: int | None = Field(default=None, ge=1)


class Capability(StrictModel):
    model: str
    profile_revision: str
    capabilities: list[Literal["chat", "asr", "tts", "tool_calls"]]
    languages: list[str] | None = None
    formats: list[str] | None = None
    limits: Limits | None = None


class Cancellation(StrictModel):
    supported: bool
    termination_evidence: bool


class Describe(StrictModel):
    identity: RuntimeIdentity
    capabilities: list[Capability] = Field(min_length=1)
    cancellation: Cancellation
    observed_at: datetime


class Readiness(StrictModel):
    state: ReadinessValue
    profile_epoch: int = Field(ge=0)
    observed_at: datetime
    limits: Limits | None = None


class CancelRequest(StrictModel):
    fence_token: str = Field(min_length=16, max_length=128)


class CancelResult(StrictModel):
    attempt_id: str
    disposition: CancelValue
    observed_at: datetime


class EvidenceDetail(StrictModel):
    process_alive: bool | None = None
    terminated_at: datetime | None = None
    exit_reason: str | None = None


class ExecutionEvidence(StrictModel):
    attempt_id: str
    runtime_epoch: int = Field(ge=0)
    evidence: EvidenceValue
    detail: EvidenceDetail | None = None
    observed_at: datetime
