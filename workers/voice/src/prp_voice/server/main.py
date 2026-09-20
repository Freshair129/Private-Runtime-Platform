"""prp-voice: private worker process. Identity comes from the operator, never invented here."""

import logging

import uvicorn

from prp_voice.lifecycle import Identity, Lifecycle
from prp_voice.server.app import create_app
from prp_voice.settings import Settings

log = logging.getLogger(__name__)


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(level=settings.log_level.upper())
    identity = Identity(
        runtime_uid=settings.runtime_uid,
        physical_resource_id=settings.physical_resource_id,
        profile_hash=settings.profile_hash,
        profile_epoch=settings.profile_epoch,
        manager_uid=settings.manager_uid,
    )
    lifecycle = Lifecycle(identity)
    if not identity.is_complete:
        log.warning("worker identity incomplete; readiness will stay NOT_READY")
    uvicorn.run(
        create_app(lifecycle, service_token=settings.service_token),
        host=settings.bind_host,
        port=settings.bind_port,
        log_config=None,
    )


if __name__ == "__main__":
    main()
