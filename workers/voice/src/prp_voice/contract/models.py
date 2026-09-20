"""Worker-side contract models: re-exported from the generated module (ADR-PRP-013).

Everything below comes from ``generated.py`` except the four ``Literal`` aliases, which exist so
lifecycle and server code can name a state without importing a field annotation.
``tests/unit/test_contract_aliases.py`` keeps each alias equal to the generated field type.
"""

from typing import Literal

from prp_voice.contract.generated import (
    CancellationSupport,
    CancelRequest,
    CancelResult,
    Capability,
    Describe,
    Error,
    ErrorBody,
    EvidenceDetail,
    ExecutionEvidence,
    InvocationRequest,
    InvocationResult,
    Limits,
    Readiness,
    RuntimeIdentity,
)

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

__all__ = [
    "CancelRequest",
    "CancelResult",
    "CancelValue",
    "CancellationSupport",
    "Capability",
    "Describe",
    "Error",
    "ErrorBody",
    "ErrorCode",
    "EvidenceDetail",
    "EvidenceValue",
    "ExecutionEvidence",
    "InvocationRequest",
    "InvocationResult",
    "Limits",
    "Readiness",
    "ReadinessValue",
    "RuntimeIdentity",
]
