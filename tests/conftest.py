"""Pytest fixtures and configuration for the project.

This module provides core test infrastructure including:
- PostgreSQL testcontainer setup with automatic migrations
- Database engine and session fixtures with transaction rollback
- Dependency injection container configuration
- Mock LLM fixtures for testing AI-dependent code
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from src.infrastructure.containers.root import RootContainer
from src.infrastructure.db.postgres.client import DatabaseClient
from src.infrastructure.db.redis.client import RedisClient
from src.infrastructure.db.redis.repository import BaseRedisRepository
from src.infrastructure.llm.llm_adapter import LLMAdapter, LLMProtocol
from tests.integration.db.integration_utils import run_migrations
from tests.schema import DummyOutputSchema


class TestDatabaseClient(DatabaseClient):
    """DatabaseClient substitute for tests.

    Wraps an existing test session so that repositories receive
    the same transactional session managed by the test fixture.
    No commit or rollback happens here — the test fixture controls the transaction.
    """

    def __init__(self, test_session: AsyncSession) -> None:
        self._test_session = test_session

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield the shared test session without commit/rollback."""
        yield self._test_session


@pytest.fixture(scope="session")
def postgres_container() -> str:
    """Provide a PostgreSQL testcontainer with applied migrations.

    Spins up a PostgreSQL 16 container, runs Alembic migrations,
    and provides the async connection URL for the test session.

    Yields:
        Connection URL string compatible with asyncpg driver.
    """
    with PostgresContainer("postgres:16-alpine") as postgres:
        connection_url = postgres.get_connection_url().replace("psycopg2", "asyncpg")

        run_migrations(connection_url)

        yield connection_url


@pytest_asyncio.fixture(scope="function")
async def db_engine(postgres_container: str) -> AsyncGenerator[AsyncEngine, None]:
    """Provide an async SQLAlchemy engine for each test function.

    Uses NullPool to avoid connection pooling issues in tests.
    Engine is properly disposed after each test.

    Args:
        postgres_container: Connection URL from the testcontainer fixture.

    Yields:
        Configured AsyncEngine instance.
    """
    engine = create_async_engine(
        url=postgres_container,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session with automatic transaction rollback.

    Each test runs in an isolated transaction that is rolled back after completion,
    ensuring test isolation without manual cleanup.

    Args:
        db_engine: SQLAlchemy async engine fixture.

    Yields:
        AsyncSession bound to a transaction that will be rolled back.
    """
    async with db_engine.connect() as connection:
        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
        )

        async with session_factory() as test_session:
            yield test_session

        await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def db_client(session: AsyncSession) -> AsyncGenerator[DatabaseClient, None]:
    """Provide a TestDatabaseClient wrapping the transactional test session.

    Args:
        session: Test session with transaction rollback.

    Yields:
        DatabaseClient-compatible object for repository construction.
    """
    yield TestDatabaseClient(session)


@pytest.fixture(scope="session")
def redis_container() -> str:
    """Provide a Redis testcontainer for integration tests.

    Spins up a Redis 7 Alpine container with password authentication
    and provides the connection URL for the test session.

    Yields:
        Redis connection URL string (e.g., ``redis://:password@host:port/0``).
    """
    with RedisContainer("redis:7-alpine", password="test_redis_pass") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        yield f"redis://:test_redis_pass@{host}:{port}/0"


@pytest_asyncio.fixture(scope="function")
async def redis_client(redis_container: str) -> AsyncGenerator[RedisClient, None]:
    """Provide an async RedisClient for each test function.

    After each test the database is flushed to ensure isolation,
    then the client connection pool is closed.

    Args:
        redis_container: Connection URL from the testcontainer fixture.

    Yields:
        Configured RedisClient instance.
    """
    test_redis_client = RedisClient(redis_url=redis_container, max_connections=5)
    yield test_redis_client
    await test_redis_client.client.flushdb()
    await test_redis_client.close()


@pytest_asyncio.fixture(scope="function")
async def redis_repository(redis_client: RedisClient) -> BaseRedisRepository:
    """Provide a BaseRedisRepository backed by the test RedisClient.

    Args:
        redis_client: Test RedisClient connected to the testcontainer.

    Returns:
        BaseRedisRepository instance for integration testing.
    """
    return BaseRedisRepository(redis_client)


@pytest.fixture(scope="session")
def container() -> RootContainer:
    """Provide a configured dependency injection container for tests.

    The container is wired to the tests module, allowing automatic
    dependency injection in test functions.

    Returns:
        Configured RootContainer instance with wired dependencies.
    """
    container = RootContainer()
    container.wire(modules=["tests"])
    return container


@pytest.fixture
def mock_llm() -> LLMProtocol:
    """Provide a mock LLM instance conforming to LLMProtocol.

    All LLM methods are mocked with appropriate return types.
    Use this fixture when testing code that depends on LLM functionality
    without making actual API calls.

    Returns:
        Mock LLMProtocol instance with pre-configured method stubs.
    """
    llm_mock = MagicMock(spec=LLMProtocol)
    llm_mock.model_name = "gpt-4"
    llm_mock.async_client = MagicMock()
    llm_mock.ainvoke = AsyncMock()
    llm_mock.astream = AsyncMock()
    llm_mock.bind_tools = MagicMock(return_value=llm_mock)
    llm_mock.with_config = MagicMock(return_value=llm_mock)
    llm_mock.with_structured_output = MagicMock(return_value=llm_mock)
    return cast(LLMProtocol, llm_mock)


@pytest.fixture(autouse=True)
def override_llm(container: RootContainer, mock_llm: LLMProtocol) -> None:
    """Automatically override the LLM dependency with a mock for all tests.

    This fixture runs automatically for every test, replacing the real LLM
    with a mock to avoid external API calls and ensure test determinism.

    Args:
        container: Dependency injection container.
        mock_llm: Mock LLM instance to inject.

    Yields:
        None, but maintains the override context for the test duration.
    """
    with container.infrastructure.llm.override(mock_llm):
        yield


@pytest.fixture
def mock_llm_adapter() -> LLMAdapter:
    """Provide a mock LLMAdapter instance for testing adapter-dependent code.

    The adapter is pre-configured with mock responses for both
    standard and structured invocations.

    Returns:
        Mock LLMAdapter with ainvoke and structured_ainvoke methods.
    """
    llm_adapter_mock = MagicMock(spec=LLMAdapter)
    llm_adapter_mock.ainvoke = AsyncMock(return_value="llm adapter ainvoke")
    llm_adapter_mock.structured_ainvoke = AsyncMock(
        return_value=DummyOutputSchema(output="llm adapter structuted output"),
    )

    return cast(LLMAdapter, llm_adapter_mock)
