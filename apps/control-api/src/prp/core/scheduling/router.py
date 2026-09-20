"""Candidate selection. Select only; committing requires Admission (ADR-PRP-002)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta

from prp.core.observability.model import Observation, ReadinessState
from prp.core.scheduling.model import Candidate, RoutePlan


def rank_candidates(
    candidates: Sequence[Candidate],
    observations: Mapping[str, Observation],
    *,
    preference: Sequence[str],
    now: datetime,
    max_staleness: timedelta,
) -> RoutePlan:
    """Rank READY candidates with fresh, epoch-matching observations by pool preference.

    NOT_READY and UNKNOWN nodes are excluded rather than guessed at; stale observations are not
    evidence (ARCH-PRP §5: budgets are measured profiles plus active reservations).
    """
    eligible: list[Candidate] = []
    for candidate in candidates:
        observation = observations.get(candidate.node_id)
        if observation is None or observation.state is not ReadinessState.READY:
            continue
        if observation.profile_epoch != candidate.profile_epoch:
            continue
        if now - observation.observed_at > max_staleness:
            continue
        eligible.append(candidate)

    order = {label: index for index, label in enumerate(preference)}
    ranked = tuple(sorted(eligible, key=lambda c: order.get(c.pool_label, len(order))))
    reason = (
        "no eligible candidate"
        if not ranked
        else f"{len(ranked)} eligible; preference {','.join(preference)}"
    )
    return RoutePlan(ranked=ranked, reason=reason)
