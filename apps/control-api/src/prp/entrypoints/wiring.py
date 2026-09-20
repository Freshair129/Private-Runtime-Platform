"""Composition root (SDD-PRP-REPO §6.3)."""

from prp.api.app import Dependencies
from prp.platform.clock import SystemClock
from prp.settings import Settings


def build_dependencies(settings: Settings) -> Dependencies:
    """M3: no adapters exist yet, so every port stays ``None`` and the API fails closed.

    M4 replaces the ``None`` values with adapters selected by the WP24 fit-gap dispositions.
    """
    del settings
    return Dependencies(key_verifier=None, clock=SystemClock())
