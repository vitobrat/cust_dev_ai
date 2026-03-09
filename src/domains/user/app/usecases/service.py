"""Business logic service for the User domain."""

import uuid

from src.configs.log.logger import get_logger
from src.domains.user.db.postgres.repository import UserRepository
from src.domains.user.exceptions import (
    UserDeletionFailed,
    UserGetFailed,
    UserUpdateFailed,
)
from src.schemas.user import (
    CreateUserSchema,
    UpdateUserSchema,
    UserRelEntitySchema,
)


class UserService:
    """Service layer for user business logic.

    Encapsulates CRUD operations for user entities, acting as the boundary
    between the HTTP layer and the persistence layer.

    Attributes:
        _users_repository: Repository for user persistence operations.
    """

    def __init__(self, users_repository: UserRepository) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._users_repository = users_repository

    async def create_user(self, create_user_data: CreateUserSchema) -> UserRelEntitySchema:
        """Persist a new user entity.

        Args:
            create_user_data: Validated creation payload.

        Returns:
            Newly created user entity with generated ID.
        """
        return await self._users_repository.create(create_user_data)

    async def get_user(self, user_id: uuid.UUID) -> UserRelEntitySchema:
        """Retrieve a single user by its identifier.

        Args:
            user_id: UUID of the user to retrieve.

        Returns:
            User entity with loaded relations if found.

        Raises:
            UserGetFailed: If no user with the given ID exists.
        """
        user = await self._users_repository.get_by_id(user_id)

        if user is None:
            self._logger.error("User not found: %s", user_id)
            raise UserGetFailed(f"User with id={user_id} does not exist.")

        return user

    async def get_users(self, limit: int = 10, offset: int = 0) -> list[UserRelEntitySchema]:
        """Retrieve a paginated list of users.

        Args:
            limit: Maximum number of records to return. Defaults to 10.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of user entities (may be empty).
        """
        return await self._users_repository.get_all(limit, offset)

    async def count_users(self) -> int:
        """Return the total number of stored users.

        Returns:
            Integer count of user records.
        """
        return await self._users_repository.get_count()

    async def update_user(
        self,
        user_id: uuid.UUID,
        update_user_data: UpdateUserSchema,
    ) -> UserRelEntitySchema:
        """Apply a partial update to an existing user.

        Args:
            user_id: UUID of the user to update.
            update_user_data: Partial schema; only set fields are applied.

        Returns:
            Updated user entity.

        Raises:
            UserUpdateFailed: If no user with the given ID exists.
        """
        updated_user = await self._users_repository.update_by_id(user_id, update_user_data)

        if updated_user is None:
            self._logger.error("User not found for update: %s", user_id)
            raise UserUpdateFailed(f"User with id={user_id} does not exist.")

        return updated_user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Delete a user by its identifier.

        Args:
            user_id: UUID of the user to delete.

        Raises:
            UserDeletionFailed: If no user with the given ID exists.
        """
        deleted_id = await self._users_repository.delete_by_id(user_id)

        if deleted_id is None:
            self._logger.error("User not found for deletion: %s", user_id)
            raise UserDeletionFailed(f"User with id={user_id} does not exist.")
