"""Pure state rules for dispatch, cancellation, deadlines and settlement (ARCH-PRP §6)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from prp.core.execution.model import (
    Attempt,
    ExecutionStatus,
    Job,
    OutboxRecord,
    OutboxState,
    Outcome,
    ResultEnvelope,
)

_PRE_DISPATCH = frozenset({ExecutionStatus.QUEUED, ExecutionStatus.RESERVED})
_TERMINAL_OUTCOMES = frozenset(
    {Outcome.SUCCEEDED, Outcome.FAILED, Outcome.TIMED_OUT, Outcome.CANCELLED}
)


class SettlementRejectedError(Exception):
    pass


def can_settle(attempt: Attempt, result: ResultEnvelope, *, content_revoked: bool) -> bool:
    """A result is accepted only when every identity dimension matches and content is unrevoked."""
    return (
        result.attempt_id == attempt.id
        and result.invocation_id == attempt.invocation_id
        and result.profile_epoch == attempt.profile_epoch
        and result.fence_token == attempt.fence_token
        and not content_revoked
    )


def settle(job: Job, outcome: Outcome, *, at: datetime) -> Job:
    """Settle exactly once; a duplicate callback or poll result must be ignored or reconciled."""
    if job.settled_at is not None or job.outcome in _TERMINAL_OUTCOMES:
        raise SettlementRejectedError(f"job {job.id} already settled as {job.outcome.value}")
    if outcome not in _TERMINAL_OUTCOMES:
        raise SettlementRejectedError(f"{outcome.value} is not a terminal outcome")
    return replace(job, outcome=outcome, execution=ExecutionStatus.FINISHED, settled_at=at)


def on_client_deadline(job: Job, *, at: datetime) -> Job:
    """The client outcome becomes TIMED_OUT; execution becomes UNKNOWN unless already FINISHED."""
    if job.outcome in _TERMINAL_OUTCOMES:
        return job
    execution = (
        ExecutionStatus.FINISHED
        if job.execution is ExecutionStatus.FINISHED
        else ExecutionStatus.UNKNOWN
    )
    return replace(job, outcome=Outcome.TIMED_OUT, execution=execution, settled_at=at)


def on_cancel_request(job: Job, *, at: datetime) -> Job:
    """Queued work cancels immediately; dispatched work only records the request (API-PRP §5)."""
    if job.outcome in _TERMINAL_OUTCOMES:
        return job
    if job.execution in _PRE_DISPATCH:
        return replace(
            job,
            outcome=Outcome.CANCELLED,
            execution=ExecutionStatus.FINISHED,
            cancellation_requested=True,
            settled_at=at,
        )
    return replace(job, cancellation_requested=True)


def claim_outbox(record: OutboxRecord, *, dispatcher_id: str) -> OutboxRecord:
    """Only PENDING records can be claimed; a second dispatcher must never blindly resend."""
    if record.state is not OutboxState.PENDING:
        raise SettlementRejectedError(
            f"outbox {record.attempt_id} is {record.state.value}, not PENDING"
        )
    return replace(record, state=OutboxState.CLAIMED, claimed_by=dispatcher_id)


def mark_dispatching(record: OutboxRecord, *, dispatcher_id: str) -> OutboxRecord:
    """Marked DISPATCHING before the network send; failure afterwards is UNKNOWN, not a retry."""
    if record.state is not OutboxState.CLAIMED or record.claimed_by != dispatcher_id:
        raise SettlementRejectedError(
            f"outbox {record.attempt_id} is not claimed by {dispatcher_id}"
        )
    return replace(record, state=OutboxState.DISPATCHING)
