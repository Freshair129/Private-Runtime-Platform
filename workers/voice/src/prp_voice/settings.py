"""Worker settings. Only environment variable names live here (Coding-Standards §7).

Identity values are assigned by the operator at enrollment (OPS-PRP RB02, management registerNode)
and must match what the control plane recorded; the worker never invents them.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

ENV_PREFIX = "PRP_VOICE_"


@dataclass(frozen=True, slots=True)
class Settings:
    bind_host: str = "127.0.0.1"
    bind_port: int = 8090
    log_level: str = "INFO"
    runtime_uid: str = ""
    physical_resource_id: str = ""
    profile_hash: str = ""
    profile_epoch: int = 0
    manager_uid: str | None = None
    service_token: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if env is None else env
        defaults = cls()

        def get(name: str, default: str) -> str:
            return source.get(f"{ENV_PREFIX}{name}", default)

        return cls(
            bind_host=get("BIND_HOST", defaults.bind_host),
            bind_port=int(get("BIND_PORT", str(defaults.bind_port))),
            log_level=get("LOG_LEVEL", defaults.log_level),
            runtime_uid=get("RUNTIME_UID", ""),
            physical_resource_id=get("PHYSICAL_RESOURCE_ID", ""),
            profile_hash=get("PROFILE_HASH", ""),
            profile_epoch=int(get("PROFILE_EPOCH", "0")),
            manager_uid=source.get(f"{ENV_PREFIX}MANAGER_UID") or None,
            service_token=source.get(f"{ENV_PREFIX}SERVICE_TOKEN") or None,
        )
