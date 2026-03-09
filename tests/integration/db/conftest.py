"""Pytest fixtures for integration database tests.

This module provides factory fixtures for creating test entities
with real database persistence via repositories.
"""

import uuid
from collections.abc import AsyncGenerator, Callable

import pytest_asyncio
from polyfactory.factories.pydantic_factory import ModelFactory

from src.domains.interview.db.postgres.repository import InterviewRepository
from src.domains.persona.db.postgres.repository import PersonaRepository
from src.domains.sub_interview.db.postgres.repository import (
    SubInterviewRepository,
)
from src.domains.task.db.postgres.repository import TaskRepository
from src.domains.user.db.postgres.repository import UserRepository
from src.infrastructure.db.postgres.client import DatabaseClient
from src.schemas.interview import (
    CreateInterviewSchema,
    InterviewRelEntitySchema,
)
from src.schemas.persona import CreatePersonaSchema, PersonaRelEntitySchema
from src.schemas.sub_interview import (
    CreateSubInterviewSchema,
    SubInterviewRelEntitySchema,
)
from src.schemas.task import CreateTaskSchema, TaskRelEntitySchema
from src.schemas.user import CreateUserSchema, UserRelEntitySchema


class CreateUserSchemaFactory(ModelFactory):
    """Polyfactory factory for generating CreateUserSchema instances."""

    __model__ = CreateUserSchema


class CreateInterviewSchemaFactory(ModelFactory):
    """Polyfactory factory for generating CreateInterviewSchema instances."""

    __model__ = CreateInterviewSchema


class CreatePersonaSchemaFactory(ModelFactory):
    """Polyfactory factory for generating CreatePersonaSchema instances.

    By default, generates personas with is_verified=False.
    """

    __model__ = CreatePersonaSchema

    @classmethod
    def is_verified(cls) -> bool:
        """Override default is_verified value to False.

        Returns:
            Always returns False for unverified personas by default.
        """
        return False


class CreateSubInterviewSchemaFactory(ModelFactory):
    """Polyfactory factory for generating CreateSubInterviewSchema instances."""

    __model__ = CreateSubInterviewSchema


class CreateTaskSchemaFactory(ModelFactory):
    """Polyfactory factory for generating CreateTaskSchema instances."""

    __model__ = CreateTaskSchema


@pytest_asyncio.fixture(scope="function")
def create_user_schema_factory() -> Callable[..., CreateUserSchema]:
    """Provide a factory function for building CreateUserSchema instances.

    Returns:
        Factory function that accepts keyword arguments and returns
        a CreateUserSchema instance without database persistence.
    """

    def factory(**kwargs: object) -> CreateUserSchema:
        return CreateUserSchemaFactory.build(**kwargs)

    return factory


@pytest_asyncio.fixture(scope="function")
async def user_factory(
    db_client: DatabaseClient,
) -> AsyncGenerator[Callable[..., UserRelEntitySchema], None]:
    """Provide an async factory for creating User entities in the database.

    Args:
        db_client: Test database client wrapping the transactional session.

    Yields:
        Async factory function that creates and persists User entities.
    """

    async def factory(**kwargs: object) -> UserRelEntitySchema:
        user_data = CreateUserSchemaFactory.build(**kwargs)
        repo = UserRepository(db_client)
        return await repo.create(user_data)

    yield factory


@pytest_asyncio.fixture(scope="function")
async def user(user_factory: Callable[..., UserRelEntitySchema]) -> UserRelEntitySchema:
    """Provide a single persisted User entity for tests.

    Args:
        user_factory: Factory fixture for creating users.

    Returns:
        A persisted UserRelEntitySchema instance.
    """
    return await user_factory()


@pytest_asyncio.fixture(scope="function")
def create_interview_schema_factory() -> Callable[..., CreateInterviewSchema]:
    """Provide a factory function for building CreateInterviewSchema instances.

    Returns:
        Factory function that accepts keyword arguments and returns
        a CreateInterviewSchema instance without database persistence.
    """

    def factory(**kwargs: object) -> CreateInterviewSchema:
        return CreateInterviewSchemaFactory.build(**kwargs)

    return factory


@pytest_asyncio.fixture(scope="function")
async def interview_factory(
    db_client: DatabaseClient,
    user_factory: Callable[..., UserRelEntitySchema],
) -> AsyncGenerator[Callable[..., InterviewRelEntitySchema], None]:
    """Provide an async factory for creating Interview entities in the database.

    Automatically creates a parent User if user_id is not provided.

    Args:
        db_client: Test database client wrapping the transactional session.
        user_factory: Factory for creating parent User entities.

    Yields:
        Async factory function that creates and persists Interview entities.
    """

    async def factory(
        user_id: uuid.UUID | None = None,
        **kwargs: object,
    ) -> InterviewRelEntitySchema:
        if user_id is None:
            owner = await user_factory()
            user_id = owner.id

        interview_data = CreateInterviewSchemaFactory.build(user_id=user_id, **kwargs)
        repo = InterviewRepository(db_client)
        return await repo.create(interview_data)

    yield factory


@pytest_asyncio.fixture(scope="function")
async def interview(
    interview_factory: Callable[..., InterviewRelEntitySchema],
) -> InterviewRelEntitySchema:
    """Provide a single persisted Interview entity for tests.

    Args:
        interview_factory: Factory fixture for creating interviews.

    Returns:
        A persisted InterviewRelEntitySchema instance with parent User.
    """
    return await interview_factory()


@pytest_asyncio.fixture(scope="function")
def create_persona_schema_factory() -> Callable[..., CreatePersonaSchema]:
    """Provide a factory function for building CreatePersonaSchema instances.

    Use this in tests that need to call PersonaRepository.create() directly,
    so the test itself owns the full repository call and can assert on it.

    Returns:
        Factory function that accepts keyword arguments and returns
        a CreatePersonaSchema instance without database persistence.
    """

    def factory(**kwargs: object) -> CreatePersonaSchema:
        return CreatePersonaSchemaFactory.build(**kwargs)

    return factory


@pytest_asyncio.fixture(scope="function")
async def persona_factory(
    db_client: DatabaseClient,
    interview_factory: Callable[..., InterviewRelEntitySchema],
) -> AsyncGenerator[Callable[..., PersonaRelEntitySchema], None]:
    """Provide an async factory for creating Persona entities in the database.

    Automatically creates a parent Interview (and User) if interview_id is not provided.

    Args:
        db_client: Test database client wrapping the transactional session.
        interview_factory: Factory for creating parent Interview entities.

    Yields:
        Async factory function that creates and persists Persona entities.
    """

    async def factory(
        interview_id: uuid.UUID | None = None,
        **kwargs: object,
    ) -> PersonaRelEntitySchema:
        if interview_id is None:
            parent_interview = await interview_factory()
            interview_id = parent_interview.id

        persona_data = CreatePersonaSchemaFactory.build(interview_id=interview_id, **kwargs)
        repo = PersonaRepository(db_client)
        return await repo.create(persona_data)

    yield factory


@pytest_asyncio.fixture(scope="function")
async def persona(
    persona_factory: Callable[..., PersonaRelEntitySchema],
) -> PersonaRelEntitySchema:
    """Provide a single persisted Persona entity for tests.

    Args:
        persona_factory: Factory fixture for creating personas.

    Returns:
        A persisted PersonaRelEntitySchema instance with parent Interview.
    """
    return await persona_factory()


@pytest_asyncio.fixture(scope="function")
def create_sub_interview_schema_factory() -> Callable[..., CreateSubInterviewSchema]:
    """Provide a factory function for building CreateSubInterviewSchema instances.

    Returns:
        Factory function that accepts keyword arguments and returns
        a CreateSubInterviewSchema instance without database persistence.
    """

    def factory(**kwargs: object) -> CreateSubInterviewSchema:
        return CreateSubInterviewSchemaFactory.build(**kwargs)

    return factory


@pytest_asyncio.fixture(scope="function")
async def sub_interview_factory(
    db_client: DatabaseClient,
    interview_factory: Callable[..., InterviewRelEntitySchema],
) -> AsyncGenerator[Callable[..., SubInterviewRelEntitySchema], None]:
    """Provide an async factory for creating SubInterview entities in the database.

    Automatically creates a parent Interview (and User) if interview_id is not provided.

    Args:
        db_client: Test database client wrapping the transactional session.
        interview_factory: Factory for creating parent Interview entities.

    Yields:
        Async factory function that creates and persists SubInterview entities.
    """

    async def factory(
        interview_id: uuid.UUID | None = None,
        **kwargs: object,
    ) -> SubInterviewRelEntitySchema:
        if interview_id is None:
            parent_interview = await interview_factory()
            interview_id = parent_interview.id

        sub_interview_data = CreateSubInterviewSchemaFactory.build(interview_id=interview_id, **kwargs)
        repo = SubInterviewRepository(db_client)
        return await repo.create(sub_interview_data)

    yield factory


@pytest_asyncio.fixture(scope="function")
async def sub_interview(
    sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
) -> SubInterviewRelEntitySchema:
    """Provide a single persisted SubInterview entity for tests.

    Args:
        sub_interview_factory: Factory fixture for creating sub-interviews.

    Returns:
        A persisted SubInterviewRelEntitySchema instance with parent Interview.
    """
    return await sub_interview_factory()


@pytest_asyncio.fixture(scope="function")
def create_task_schema_factory() -> Callable[..., CreateTaskSchema]:
    """Provide a factory function for building CreateTaskSchema instances.

    Returns:
        Factory function that accepts keyword arguments and returns
        a CreateTaskSchema instance without database persistence.
    """

    def factory(**kwargs: object) -> CreateTaskSchema:
        return CreateTaskSchemaFactory.build(**kwargs)

    return factory


@pytest_asyncio.fixture(scope="function")
async def task_factory(
    db_client: DatabaseClient,
    user_factory: Callable[..., UserRelEntitySchema],
) -> AsyncGenerator[Callable[..., TaskRelEntitySchema], None]:
    """Provide an async factory for creating Task entities in the database.

    Automatically creates a parent User if user_id is not provided.

    Args:
        db_client: Test database client wrapping the transactional session.
        user_factory: Factory for creating parent User entities.

    Yields:
        Async factory function that creates and persists Task entities.
    """

    async def factory(
        user_id: uuid.UUID | None = None,
        **kwargs: object,
    ) -> TaskRelEntitySchema:
        if user_id is None:
            owner = await user_factory()
            user_id = owner.id

        task_data = CreateTaskSchemaFactory.build(user_id=user_id, **kwargs)
        repo = TaskRepository(db_client)
        return await repo.create(task_data)

    yield factory


@pytest_asyncio.fixture(scope="function")
async def task(task_factory: Callable[..., TaskRelEntitySchema]) -> TaskRelEntitySchema:
    """Provide a single persisted Task entity for tests.

    Args:
        task_factory: Factory fixture for creating tasks.

    Returns:
        A persisted TaskRelEntitySchema instance with parent User.
    """
    return await task_factory()
