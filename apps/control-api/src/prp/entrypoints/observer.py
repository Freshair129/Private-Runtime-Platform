"""prp-observer: critical observer independent of any dashboard (ARCH-PRP §2).

M3: refuses to start because no RuntimeDescriber or ObservationSink adapter exists. Missing
observations must stay missing, never be fabricated as healthy.
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
        "observer refuses to start: no runtime describer or observation sink configured (M4)",
        extra={"prp": {"process": "observer", "exit_code": EXIT_NOT_CONFIGURED}},
    )
    return EXIT_NOT_CONFIGURED


if __name__ == "__main__":
    raise SystemExit(main())
