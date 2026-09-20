"""Unit evidence for uncertain-execution fencing and cancellation semantics (FR-020, FR-021).

Partial: acceptance PRP-AT-020/021 also need a killed coordinator and a live worker; those stay
NOT_RUN until integration evidence exists.
"""

from datetime import UTC, datetime, timedelta

import pytest

from prp.core.execution.model import (
    Attempt,
    ExecutionStatus,
    Job,
    Kind,
    OutboxRecord,
    OutboxState,
    Outcome,
    ResultEnvelope,
)
from prp.core.execution.rules import (
    SettlementRejectedError,
    can_settle,
    claim_outbox,
    mark_dispatching,
    on_cancel_request,
    on_client_deadline,
    settle,
)

pytestmark = [pytest.mark.req("PRP-FR-020"), pytest.mark.req("PRP-FR-021")]

NOW = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)


def make_job(execution: ExecutionStatus, outcome: Outcome = Outcome.PENDING) -> Job:
    return Job(
        id="job-1",
        invocation_id="inv-1",
        kind=Kind.ASR,
        outcome=outcome,
        execution=execution,
        cancellation_requested=False,
        created_at=NOW,
        deadline_at=NOW + timedelta(seconds=180),
    )


ATTEMPT = Attempt(
    id="att-1",
    invocation_id="inv-1",
    node_id="node-a",
    profile_epoch=7,
    fence_token="fence-0123456789abcdef",
    execution=ExecutionStatus.DISPATCHED,
)


def make_result(**overrides: object) -> ResultEnvelope:
    values: dict[str, object] = {
        "invocation_id": "inv-1",
        "attempt_id": "att-1",
        "runtime_uid": "rt-a",
        "physical_resource_id": "hostA/GPU-0",
        "profile_epoch": 7,
        "fence_token": "fence-0123456789abcdef",
    }
    values.update(overrides)
    return ResultEnvelope(**values)  # type: ignore[arg-type]


def test_result_settles_only_when_every_identity_dimension_matches() -> None:
    assert can_settle(ATTEMPT, make_result(), content_revoked=False)
    assert not can_settle(ATTEMPT, make_result(profile_epoch=8), content_revoked=False)
    assert not can_settle(
        ATTEMPT, make_result(fence_token="other-fence-token-xx"), content_revoked=False
    )
    assert not can_settle(ATTEMPT, make_result(attempt_id="att-2"), content_revoked=False)
    assert not can_settle(ATTEMPT, make_result(), content_revoked=True)


def test_result_is_accepted_once() -> None:
    settled = settle(make_job(ExecutionStatus.RUNNING), Outcome.SUCCEEDED, at=NOW)
    assert settled.outcome is Outcome.SUCCEEDED and settled.execution is ExecutionStatus.FINISHED
    with pytest.raises(SettlementRejectedError):
        settle(settled, Outcome.SUCCEEDED, at=NOW)
    with pytest.raises(SettlementRejectedError):
        settle(make_job(ExecutionStatus.RUNNING), Outcome.PENDING, at=NOW)


def test_client_deadline_never_proves_compute_stopped() -> None:
    timed_out = on_client_deadline(make_job(ExecutionStatus.RUNNING), at=NOW)
    assert timed_out.outcome is Outcome.TIMED_OUT
    assert timed_out.execution is ExecutionStatus.UNKNOWN


def test_client_deadline_keeps_finished_execution_finished() -> None:
    job = on_client_deadline(make_job(ExecutionStatus.FINISHED), at=NOW)
    assert (job.outcome, job.execution) == (Outcome.TIMED_OUT, ExecutionStatus.FINISHED)


def test_cancel_before_dispatch_finishes_immediately() -> None:
    job = on_cancel_request(make_job(ExecutionStatus.QUEUED), at=NOW)
    assert (job.outcome, job.execution) == (Outcome.CANCELLED, ExecutionStatus.FINISHED)
    assert job.cancellation_requested is True


def test_cancel_after_dispatch_only_records_the_request() -> None:
    job = on_cancel_request(make_job(ExecutionStatus.RUNNING), at=NOW)
    assert job.cancellation_requested is True
    assert (job.outcome, job.execution) == (Outcome.PENDING, ExecutionStatus.RUNNING)
    assert on_cancel_request(job, at=NOW) == job


def test_second_dispatcher_cannot_reclaim_or_resend() -> None:
    record = OutboxRecord(
        attempt_id="att-1", node_id="node-a", profile_epoch=7, state=OutboxState.PENDING
    )
    claimed = claim_outbox(record, dispatcher_id="d1")
    assert claimed.state is OutboxState.CLAIMED and claimed.claimed_by == "d1"
    with pytest.raises(SettlementRejectedError):
        claim_outbox(claimed, dispatcher_id="d2")
    with pytest.raises(SettlementRejectedError):
        mark_dispatching(claimed, dispatcher_id="d2")
    assert mark_dispatching(claimed, dispatcher_id="d1").state is OutboxState.DISPATCHING
