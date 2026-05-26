"""Standard response envelope helpers and exception handlers for the RapidCull API.

Every /api/v1/* endpoint returns one of two shapes:

  Success:  {"ok": true,  "data": <payload>, "meta": <obj-or-null>}
  Error:    {"ok": false, "error": {"code": "<UPPER_SNAKE>", "message": "<str>",
                                    "details": <obj-or-null>}}
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Structured API error that maps to the standard error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Any = None,
        http_status: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.http_status = http_status


# ---------------------------------------------------------------------------
# Envelope builder helpers
# ---------------------------------------------------------------------------


def ok(data: Any, meta: Any = None) -> dict[str, Any]:
    """Build a success envelope."""
    return {"ok": True, "data": data, "meta": meta}


def err(
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    """Build an error envelope (body only — HTTP status set by the caller)."""
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle ApiError instances — emits the error envelope."""
    if not isinstance(exc, ApiError):
        return JSONResponse(
            status_code=500,
            content=err("INTERNAL_ERROR", "Unexpected exception type in ApiError handler."),
        )
    return JSONResponse(
        status_code=exc.http_status,
        content=err(exc.code, exc.message, exc.details),
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert FastAPI/Starlette HTTPException to the error envelope."""
    if not isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=500,
            content=err("INTERNAL_ERROR", "Unexpected exception type in HTTPException handler."),
        )
    code = f"HTTP_{exc.status_code}"
    message = str(exc.detail) if exc.detail is not None else "An error occurred."
    return JSONResponse(
        status_code=exc.status_code,
        content=err(code, message),
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert Pydantic RequestValidationError to the error envelope."""
    if not isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=500,
            content=err("INTERNAL_ERROR", "Unexpected exception type in validation handler."),
        )
    return JSONResponse(
        status_code=422,
        content=err(
            "VALIDATION_ERROR",
            "Request validation failed.",
            details=exc.errors(),
        ),
    )


def register_handlers(app: Any) -> None:
    """Register all envelope exception handlers on a FastAPI application."""
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
