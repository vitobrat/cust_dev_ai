"""Base repository module for PostgreSQL CRUD operations.

This module provides an abstract base class for implementing repository pattern
with DatabaseClient-managed sessions.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar

from src.infrastructure.db.postgres.client import DatabaseClient

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
RelEntityType = TypeVar("RelEntityType")


class BaseCRUDRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType, RelEntityType]):
    """Abstract base repository for CRUD operations on database entities.

    Each public method opens its own session via ``DatabaseClient.session()``,
    ensuring per-operation transaction boundaries (auto-commit on success,
    rollback on exception).

    Type Parameters:
        ModelType: SQLAlchemy ORM model type.
        CreateSchemaType: Pydantic schema for entity creation.
        UpdateSchemaType: Pydantic schema for entity updates.
        RelEntityType: Pydantic schema representing the entity with relations.

    Attributes:
        model: SQLAlchemy ORM model class associated with this repository.
    """

    model: Type[ModelType]

    def __init__(self, db_client: DatabaseClient) -> None:
        """Initialize repository with database client.

        Args:
            db_client: Database client that provides per-operation sessions.
        """
        self._db_client = db_client

    @abstractmethod
    async def create(self, create_data: CreateSchemaType) -> RelEntityType:
        """Create a new entity in the database.

        Args:
            create_data: Schema containing data for entity creation.

        Returns:
            Created entity as a validated schema.
        """
        ...

    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[RelEntityType]:
        """Retrieve an entity by its unique identifier.

        Args:
            entity_id: UUID of the entity to retrieve.

        Returns:
            Entity schema if found, None otherwise.
        """
        ...

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[RelEntityType]:
        """Retrieve multiple entities with pagination.

        Args:
            limit: Maximum number of entities to return. Defaults to 100.
            offset: Number of entities to skip. Defaults to 0.

        Returns:
            List of entity schemas.
        """
        ...

    @abstractmethod
    async def get_count(self) -> int:
        """Get total count of entities in the repository.

        Returns:
            Total number of entities.
        """
        ...

    @abstractmethod
    async def update_by_id(self, entity_id: uuid.UUID, update_data: UpdateSchemaType) -> Optional[RelEntityType]:
        """Update an existing entity by its identifier.

        Args:
            entity_id: UUID of the entity to update.
            data: Schema containing update data.

        Returns:
            Updated entity schema if found, None otherwise.
        """
        ...

    @abstractmethod
    async def delete_by_id(self, entity_id: uuid.UUID) -> Optional[uuid.UUID]:
        """Delete an entity by its identifier.

        Args:
            entity_id: UUID of the entity to delete.

        Returns:
            UUID of deleted entity if found, None otherwise.
        """
        ...
