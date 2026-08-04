"""Unit tests for domain exception hierarchy."""

from __future__ import annotations

from taxos.core.exceptions import (
    ConflictError,
    DomainValidationError,
    InfrastructureError,
    NotFoundError,
    TaxOSError,
)


class TestExceptionHierarchy:
    """Tests for the exception hierarchy."""

    def test_base_error_defaults(self) -> None:
        err = TaxOSError()
        assert err.message == "An unexpected error occurred"
        assert err.code == "TAXOS_ERROR"
        assert err.details == {}

    def test_not_found_error(self) -> None:
        err = NotFoundError("User not found", details={"user_id": "123"})
        assert err.code == "NOT_FOUND"
        assert err.details == {"user_id": "123"}
        assert isinstance(err, TaxOSError)

    def test_conflict_error(self) -> None:
        err = ConflictError()
        assert err.code == "CONFLICT"
        assert isinstance(err, TaxOSError)

    def test_validation_error(self) -> None:
        err = DomainValidationError("Invalid amount")
        assert err.code == "VALIDATION_ERROR"

    def test_infrastructure_error(self) -> None:
        err = InfrastructureError("DB connection lost")
        assert err.code == "INFRASTRUCTURE_ERROR"

    def test_custom_code(self) -> None:
        err = TaxOSError("custom", code="CUSTOM_CODE")
        assert err.code == "CUSTOM_CODE"
