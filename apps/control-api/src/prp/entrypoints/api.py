"""prp-api: ASGI web process. Scale by adding processes; never load a model here."""

import uvicorn

from prp.api.app import create_app
from prp.entrypoints.wiring import build_dependencies
from prp.platform.logging import configure_logging
from prp.settings import Settings


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    uvicorn.run(
        create_app(settings, build_dependencies(settings)),
        host=settings.bind_host,
        port=settings.bind_port,
        log_config=None,
    )


if __name__ == "__main__":
    main()
