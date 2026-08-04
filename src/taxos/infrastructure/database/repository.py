"""Generic SQLAlchemy repository implementation.

Concrete implementation of the AbstractRepository port using
SQLAlchemy async sessions.
"""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.application.interfaces.repositories import AbstractRepository
from taxos.infrastructure.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class SQLAlchemyRepository(AbstractRepository[ModelT], Generic[ModelT]):
    """Generic async repository backed by SQLAlchemy."""

    def __init__(self, session: AsyncSession, model_class: type[ModelT]) -> None:
        self._session = session
        self._model_class = model_class

    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        """Retrieve an entity by primary key."""
        return await self._session.get(self._model_class, entity_id)

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> list[ModelT]:
        """Retrieve a paginated list of entities."""
        stmt = select(self._model_class).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, entity: ModelT) -> ModelT:
        """Add a new entity to the session."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """Merge and flush an updated entity."""
        merged = await self._session.merge(entity)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by id. Returns True if found and deleted."""
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        await self._session.flush()
        return True

    async def count(self) -> int:
        """Count total entities."""
        stmt = select(func.count()).select_from(self._model_class)
        result = await self._session.execute(stmt)
        return result.scalar_one()
