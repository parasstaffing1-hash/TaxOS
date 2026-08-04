"""Base entity for all domain models.

Provides common fields (id, timestamps) shared across
all domain entities in the system.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """Base domain entity with identity and audit timestamps."""

    model_config = ConfigDict(
        from_attributes=True,
        frozen=False,
        populate_by_name=True,
    )

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
