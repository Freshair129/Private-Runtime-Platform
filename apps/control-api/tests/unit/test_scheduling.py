"""Router selects without side effects; leases quarantine on uncertainty (ADR-002, ADR-005)."""

from datetime import UTC, datetime, timedelta

import pytest

from prp.core.execution.model import ExecutionEvidence
from prp.core.observability.model import Observation, ReadinessState
from prp.core.scheduling.admission import on_client_deadline, on_termination_evidence
from prp.core.scheduling.model import Candidate, InvocationLease, LeaseState
from prp.core.scheduling.router import rank_candidates

pytestmark = [pytest.mark.req("PRP-FR-020"), pytest.mark.req("PRP-FR-044")]

NOW = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)
FRESH = timedelta(seconds=10)
A = Candidate(node_id="a", pool_label="A", profile_epoch=3)
B = Candidate(node_id="b", pool_label="B", profile_epoch=5)


def obs(
    node_id: str, epoch: int, state: ReadinessState, age: timedelta = timedelta(0)
) -> Observation:
    return Observation(node_id=node_id, profile_epoch=epoch, state=state, observed_at=NOW - age)


def test_ready_candidates_ranked_by_preference() -> None:
    observations = {"a": obs("a", 3, ReadinessState.READY), "b": obs("b", 5, ReadinessState.READY)}
    plan = rank_candidates(
        [B, A], observations, preference=("A", "B"), now=NOW, max_staleness=FRESH
    )
    assert [c.node_id for c in plan.ranked] == ["a", "b"]
    flipped = rank_candidates(
        [B, A], observations, preference=("B", "A"), now=NOW, max_staleness=FRESH
    )
    assert [c.node_id for c in flipped.ranked] == ["b", "a"]


@pytest.mark.parametrize(
    "observation",
    [
        obs("a", 3, ReadinessState.NOT_READY),
        obs("a", 3, ReadinessState.UNKNOWN),
        obs("a", 4, ReadinessState.READY),
        obs("a", 3, ReadinessState.READY, age=timedelta(seconds=11)),
    ],
    ids=["not_ready", "unknown", "epoch_mismatch", "stale"],
)
def test_unfit_observations_exclude_the_candidate(observation: Observation) -> None:
    plan = rank_candidates([A], {"a": observation}, preference=("A",), now=NOW, max_staleness=FRESH)
    assert plan.is_empty and plan.reason == "no eligible candidate"


def test_missing_observation_is_not_guessed_as_ready() -> None:
    assert rank_candidates([A], {}, preference=("A",), now=NOW, max_staleness=FRESH).is_empty


def make_lease(state: LeaseState) -> InvocationLease:
    return InvocationLease(
        id="lease-1",
        attempt_id="att-1",
        node_id="a",
        profile_epoch=3,
        slots=1,
        token_budget=512,
        expires_at=NOW + timedelta(seconds=180),
        state=state,
    )


def test_client_deadline_quarantines_instead_of_releasing() -> None:
    assert on_client_deadline(make_lease(LeaseState.HELD)).state is LeaseState.QUARANTINED
    assert on_client_deadline(make_lease(LeaseState.RELEASED)).state is LeaseState.RELEASED


def test_only_finished_evidence_releases_a_lease() -> None:
    held = make_lease(LeaseState.HELD)
    assert on_termination_evidence(held, ExecutionEvidence.RUNNING).state is LeaseState.HELD
    assert on_termination_evidence(held, ExecutionEvidence.UNKNOWN).state is LeaseState.QUARANTINED
    assert on_termination_evidence(held, ExecutionEvidence.FINISHED).state is LeaseState.RELEASED
    quarantined = make_lease(LeaseState.QUARANTINED)
    assert (
        on_termination_evidence(quarantined, ExecutionEvidence.UNKNOWN).state
        is LeaseState.QUARANTINED
    )
    assert (
        on_termination_evidence(quarantined, ExecutionEvidence.FINISHED).state
        is LeaseState.RELEASED
    )
