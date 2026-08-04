"""API middleware stack.

Provides request ID injection, structured request logging,
and global exception handling.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from taxos.core.exceptions import (
    AuthorizationError,
    ConflictError,
    DomainValidationError,
    InfrastructureError,
    NotFoundError,
    TaxOSError,
)

MAX_REQUEST_ID_LENGTH = 64

logger = structlog.get_logger(__name__)

# ── Exception → HTTP status mapping ─────────────────────────────
_EXCEPTION_STATUS_MAP: dict[type[TaxOSError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DomainValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    InfrastructureError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject a unique X-Request-ID header into every request/response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied_request_id = request.headers.get("X-Request-ID", "").strip()
        request_id = (
            supplied_request_id
            if supplied_request_id
            and len(supplied_request_id) <= MAX_REQUEST_ID_LENGTH
            and supplied_request_id.isprintable()
            else str(uuid.uuid4())
        )
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger.info(
            "request_started",
            method=request.method,
            path=str(request.url.path),
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
        )
        return response


def _build_error_body(code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    """Build a consistent error response body."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    @app.exception_handler(TaxOSError)
    async def taxos_error_handler(_request: Request, exc: TaxOSError) -> JSONResponse:
        status_code = _EXCEPTION_STATUS_MAP.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.warning(
            "domain_error",
            error_code=exc.code,
            error_message=exc.message,
            status_code=status_code,
        )
        return JSONResponse(
            status_code=status_code,
            content=_build_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        errors = exc.errors()
        formatted_errors = []
        for error in errors:
            loc = " -> ".join(str(x) for x in error["loc"])
            formatted_errors.append(
                {"location": loc, "message": error["msg"], "type": error["type"]}
            )

        logger.warning(
            "validation_error",
            path=str(request.url.path),
            errors=formatted_errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_build_error_body(
                "VALIDATION_ERROR",
                "The provided input data is invalid.",
                {"errors": formatted_errors},
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_body(
                "INTERNAL_ERROR",
                "An unexpected error occurred",
                {},
            ),
        )


_RATE_LIMIT_STORE: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60.0


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply browser security headers to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'"
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to rate limit requests based on client IP."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path.startswith(("/health", "/api/v1/health", "/docs", "/openapi.json")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        settings = getattr(request.app.state, "settings", None)
        trusted_proxies = set(getattr(settings, "TRUSTED_PROXIES", []))
        if forwarded and client_ip in trusted_proxies:
            client_ip = forwarded.split(",")[0].strip()

        default_limit = getattr(settings, "RATE_LIMIT_MAX_REQUESTS", RATE_LIMIT_MAX_REQUESTS)
        default_window = getattr(
            settings, "RATE_LIMIT_WINDOW_SECONDS", int(RATE_LIMIT_WINDOW_SECONDS)
        )
        is_auth_request = request.url.path in {"/api/v1/auth/login", "/api/v1/auth/register"}
        limit = (
            getattr(settings, "AUTH_RATE_LIMIT_MAX_REQUESTS", 10)
            if is_auth_request
            else default_limit
        )
        window = (
            getattr(settings, "AUTH_RATE_LIMIT_WINDOW_SECONDS", int(RATE_LIMIT_WINDOW_SECONDS))
            if is_auth_request
            else default_window
        )
        bucket = f"{client_ip}:{limit}:{window}"

        now = monotonic()
        _RATE_LIMIT_STORE[bucket] = [
            timestamp for timestamp in _RATE_LIMIT_STORE[bucket] if now - timestamp < window
        ]

        if len(_RATE_LIMIT_STORE[bucket]) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Please try again later.",
                        "details": {},
                    },
                },
                headers={"Retry-After": str(int(window))},
            )

        _RATE_LIMIT_STORE[bucket].append(now)
        response = await call_next(request)
        remaining = max(0, limit - len(_RATE_LIMIT_STORE[bucket]))
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
