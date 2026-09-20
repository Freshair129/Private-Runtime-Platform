"""Readiness is honest and epoch changes fence stale reservations (ARCH-PRP §11, ADR-PRP-005)."""

import pytest

from prp_voice.lifecycle import Identity, Lifecycle, Phase

pytestmark = [pytest.mark.req("PRP-FR-044"), pytest.mark.req("PRP-NFR-023")]


def test_loading_worker_is_not_ready(lifecycle: Lifecycle) -> None:
    assert lifecycle.phase is Phase.LOADING
    assert lifecycle.readiness(2).state == "NOT_READY"


def test_ready_only_for_the_current_epoch(lifecycle: Lifecycle) -> None:
    lifecycle.mark_ready()
    assert lifecycle.readiness(2).state == "READY"
    stale = lifecycle.readiness(1)
    assert stale.state == "NOT_READY" and stale.profile_epoch == 2


def test_draining_and_stopped_are_not_ready(lifecycle: Lifecycle) -> None:
    lifecycle.mark_ready()
    lifecycle.drain()
    assert lifecycle.readiness(2).state == "NOT_READY"
    lifecycle.stop()
    with pytest.raises(ValueError):
        lifecycle.mark_ready()


def test_observation_failure_is_reported_as_unknown_not_ready(lifecycle: Lifecycle) -> None:
    lifecycle.mark_ready()
    lifecycle.mark_observation_failed()
    assert lifecycle.readiness(2).state == "UNKNOWN"


def test_profile_change_bumps_epoch_and_returns_to_loading(lifecycle: Lifecycle) -> None:
    lifecycle.mark_ready()
    identity = lifecycle.bump_epoch("sha256:new-profile")
    assert identity.profile_epoch == 3 and identity.profile_hash == "sha256:new-profile"
    assert lifecycle.phase is Phase.LOADING
    assert lifecycle.readiness(2).state == "NOT_READY"


def test_incomplete_identity_cannot_become_ready() -> None:
    incomplete = Lifecycle(
        Identity(runtime_uid="", physical_resource_id="", profile_hash="", profile_epoch=0)
    )
    with pytest.raises(ValueError):
        incomplete.mark_ready()
