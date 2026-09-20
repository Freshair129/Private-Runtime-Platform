"""Typed process settings.

Only environment variable *names* live in source; values come from the process environment
(Coding-Standards §7). Route preference defaults to A before B (ARCH-PRP §5).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

ENV_PREFIX = "PRP_"


@dataclass(frozen=True, slots=True)
class Settings:
    bind_host: str = "127.0.0.1"
    bind_port: int = 8080
    log_level: str = "INFO"
    route_preference: tuple[str, ...] = ("A", "B")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if env is None else env
        defaults = cls()
        preference = source.get(
            f"{ENV_PREFIX}ROUTE_PREFERENCE", ",".join(defaults.route_preference)
        )
        return cls(
            bind_host=source.get(f"{ENV_PREFIX}BIND_HOST", defaults.bind_host),
            bind_port=int(source.get(f"{ENV_PREFIX}BIND_PORT", str(defaults.bind_port))),
            log_level=source.get(f"{ENV_PREFIX}LOG_LEVEL", defaults.log_level),
            route_preference=tuple(p.strip() for p in preference.split(",") if p.strip()),
        )
