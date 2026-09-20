"""Runtime identity, profile epoch and readiness gate (ARCH-PRP §11, §13).

Readiness is reported honestly: NOT_READY while loading or draining, UNKNOWN when the engine
cannot be observed, READY only for the epoch the control plane asked about. Health is not
qualification.
"""

from prp_voice.lifecycle.state import Identity, Lifecycle, Phase

__all__ = ["Identity", "Lifecycle", "Phase"]
