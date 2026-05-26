"""Security middleware and settings for RapidCull API (FR-043–045).

Environment variables:
    RAPIDCULL_MODE: "localhost" (default) | "lan"
        - localhost: auth disabled, permissive CORS
        - lan:       mutating endpoints require Bearer token; explicit CORS origins only
    RAPIDCULL_AUTH_TOKEN: Bearer token value (required when MODE=lan)
    RAPIDCULL_ALLOWED_ORIGINS: comma-separated allowed CORS origins (used when MODE=lan)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

_LOCALHOST_ORIGINS: list[str] = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://localhost:8000",
]
_MUTATING_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass(frozen=True)
class Settings:
    """Runtime settings derived from environment variables."""

    mode: str = "localhost"
    auth_token: str | None = None
    allowed_origins: list[str] = field(default_factory=lambda: list(_LOCALHOST_ORIGINS))


def get_settings() -> Settings:
    """Read settings from environment variables."""
    mode = os.environ.get("RAPIDCULL_MODE", "localhost").lower().strip()
    auth_token = os.environ.get("RAPIDCULL_AUTH_TOKEN") or None
    raw_origins = os.environ.get("RAPIDCULL_ALLOWED_ORIGINS", "")
    if raw_origins.strip():
        allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    else:
        allowed_origins = list(_LOCALHOST_ORIGINS)
    return Settings(mode=mode, auth_token=auth_token, allowed_origins=allowed_origins)


class AuthMiddleware(BaseHTTPMiddleware):
    """Reject mutating requests without valid Bearer token in LAN mode (FR-044)."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._settings.mode == "lan" and request.method in _MUTATING_METHODS:
            token = self._settings.auth_token
            if not token:
                return Response(
                    content='{"detail":"Server misconfiguration: auth token not configured"}',
                    status_code=503,
                    media_type="application/json",
                )
            auth_header = request.headers.get("authorization", "")
            if auth_header != f"Bearer {token}":
                return Response(
                    content='{"detail":"Unauthorized"}',
                    status_code=401,
                    media_type="application/json",
                )
        return await call_next(request)


def configure_app(app: FastAPI, settings: Settings | None = None) -> None:
    """Wire CORS and auth middleware onto app. Uses env-var settings if not provided."""
    s = settings if settings is not None else get_settings()

    # Auth middleware — added first → innermost (closest to route handler)
    app.add_middleware(AuthMiddleware, settings=s)

    # CORS middleware — added second → outermost (first to see requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
