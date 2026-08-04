"""Abstract repository interfaces (ports).

Defines the contract that all repository implementations must follow,
enabling dependency inversion between domain and infrastructure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    """Generic async repository port."""

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> T | None:
        """Retrieve an entity by its unique identifier."""
        ...

    @abstractmethod
    async def get_all(self, *, skip: int = 0, limit: int = 100) -> list[T]:
        """Retrieve a paginated list of entities."""
        ...

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Persist a new entity."""
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by its identifier. Returns True if deleted."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Return the total number of entities."""
        ...
