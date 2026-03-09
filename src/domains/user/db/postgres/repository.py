"""User repository for PostgreSQL database operations.

This module provides the repository implementation for managing user entities
in PostgreSQL database using SQLAlchemy ORM.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select

from src.domains.user.db.postgres.model import UsersOrm
from src.infrastructure.db.postgres.repository import BaseCRUDRepository
from src.schemas.user import (
    CreateUserSchema,
    UpdateUserSchema,
    UserRelEntitySchema,
)


class UserRepository(BaseCRUDRepository[UsersOrm, CreateUserSchema, UpdateUserSchema, UserRelEntitySchema]):
    """Repository for user entity CRUD operations.

    Provides async methods for creating, reading, updating, and deleting user records
    in PostgreSQL database.
    """

    async def create(
        self,
        create_data: CreateUserSchema,
    ) -> UserRelEntitySchema:
        """Create a new user record.

        Args:
            create_data: Schema containing user creation data.

        Returns:
            Created user entity with generated ID.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        async with self._db_client.session() as session:
            user = UsersOrm(name=create_data.name)
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return UserRelEntitySchema.model_validate(user)

    async def get_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[UserRelEntitySchema]:
        """Retrieve a user by its ID with related entities.

        Args:
            entity_id: UUID of the user to retrieve.

        Returns:
            User entity with loaded relations if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        async with self._db_client.session() as session:
            user = await session.get(UsersOrm, entity_id)
            if user is None:
                return None
            return UserRelEntitySchema.model_validate(user)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserRelEntitySchema]:
        """Retrieve all users with pagination.

        Args:
            limit: Maximum number of records to return. Defaults to 100.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of user entities.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        async with self._db_client.session() as session:
            query = select(UsersOrm).limit(limit).offset(offset)
            users_result = await session.execute(query)
            users = users_result.scalars().all()
            return [UserRelEntitySchema.model_validate(user) for user in users]

    async def get_count(self) -> int:
        """Get total count of users in the database.

        Returns:
            Total number of user records.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        async with self._db_client.session() as session:
            query = select(func.count()).select_from(UsersOrm)
            users_result = await session.execute(query)
            return users_result.scalar_one()

    async def update_by_id(
        self,
        entity_id: uuid.UUID,
        update_data: UpdateUserSchema,
    ) -> Optional[UserRelEntitySchema]:
        """Update a user by its ID.

        Only fields present in update_data will be modified.

        Args:
            entity_id: UUID of the user to update.
            update_data: Schema containing fields to update.

        Returns:
            Updated user entity if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        async with self._db_client.session() as session:
            user = await session.get(UsersOrm, entity_id)
            if user is None:
                return None

            update_fields = update_data.model_dump(exclude_unset=True)
            for field, user_value in update_fields.items():
                setattr(user, field, user_value)

            await session.flush()
            await session.refresh(user)
            return UserRelEntitySchema.model_validate(user)

    async def delete_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """Delete a user by its ID.

        Args:
            entity_id: UUID of the user to delete.

        Returns:
            UUID of deleted user if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        async with self._db_client.session() as session:
            user = await session.get(UsersOrm, entity_id)
            if user is None:
                return None

            await session.delete(user)
            await session.flush()
            return entity_id
