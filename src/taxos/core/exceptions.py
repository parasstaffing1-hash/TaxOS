"""Domain exception hierarchy.

All application-specific exceptions inherit from TaxOSError,
enabling consistent error handling across layers.
"""

from __future__ import annotations

from typing import Any


class TaxOSError(Exception):
    """Base exception for all TaxOS domain errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        code: str = "TAXOS_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(TaxOSError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        *,
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class ConflictError(TaxOSError):
    """Raised when an operation conflicts with existing state."""

    def __init__(
        self,
        message: str = "Resource conflict",
        *,
        code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class DomainValidationError(TaxOSError):
    """Raised when domain validation rules are violated."""

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class AuthorizationError(TaxOSError):
    """Raised when an operation is not authorized."""

    def __init__(
        self,
        message: str = "Not authorized",
        *,
        code: str = "AUTHORIZATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class InfrastructureError(TaxOSError):
    """Raised when an infrastructure operation fails (DB, network, etc.)."""

    def __init__(
        self,
        message: str = "Infrastructure error",
        *,
        code: str = "INFRASTRUCTURE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
