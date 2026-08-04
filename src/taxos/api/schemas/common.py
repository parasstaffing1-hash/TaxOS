"""Common API response schemas.

Generic response envelopes and shared schemas used
across all API endpoints.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    """Structured error detail."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    model_config = ConfigDict(frozen=True)

    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )


class ApiResponse(BaseModel, Generic[DataT]):
    """Generic success response envelope."""

    success: bool = True
    data: DataT
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated list response."""

    success: bool = True
    data: list[DataT]
    total: int
    skip: int
    limit: int
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
