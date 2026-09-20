"""prp-dispatcher: claims outbox records, marks DISPATCHING, then sends (ARCH-PRP §6).

M3: refuses to start because no OutboxStore or RuntimeInvoker adapter exists. A dispatcher that
cannot prove its send state must not run.
"""

import logging

from prp.platform.logging import configure_logging
from prp.settings import Settings

EXIT_NOT_CONFIGURED = 3
log = logging.getLogger(__name__)


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    log.error(
        "dispatcher refuses to start: no outbox store or runtime invoker configured (M4)",
        extra={"prp": {"process": "dispatcher", "exit_code": EXIT_NOT_CONFIGURED}},
    )
    return EXIT_NOT_CONFIGURED


if __name__ == "__main__":
    raise SystemExit(main())
