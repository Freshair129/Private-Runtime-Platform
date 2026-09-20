"""ASGI application factory."""

from dataclasses import dataclass, field

from fastapi import FastAPI

from prp import __version__
from prp.api.errors import install_error_handlers
from prp.api.request_id import RequestIdMiddleware
from prp.api.routes import build_router
from prp.api.security import ClientKeyAuth
from prp.core.access.ports import KeyVerifier
from prp.platform.clock import Clock, SystemClock
from prp.settings import Settings


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Ports handed in by the composition root; ``None`` means not configured and fails closed."""

    key_verifier: KeyVerifier | None = None
    clock: Clock = field(default_factory=SystemClock)


def create_app(settings: Settings, deps: Dependencies | None = None) -> FastAPI:
    deps = deps or Dependencies()
    app = FastAPI(
        title="PRP - Private Runtime Platform",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    app.add_middleware(RequestIdMiddleware)
    install_error_handlers(app)
    app.include_router(build_router(ClientKeyAuth(deps.key_verifier, deps.clock)))
    return app
