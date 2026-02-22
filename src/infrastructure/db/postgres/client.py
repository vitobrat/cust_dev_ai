"""PostgreSQL database client with connection pooling and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseClient:
    """Async PostgreSQL database client with connection pooling.

    Provides session management with automatic transaction handling,
    connection pooling, and graceful shutdown capabilities.

    Attributes:
        _engine: SQLAlchemy async engine instance.
        _session_factory: Factory for creating async database sessions.
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 10,
        echo: bool = False,
    ) -> None:
        """Initialize database client with connection pool.

        Args:
            database_url: PostgreSQL connection URL (e.g., postgresql+asyncpg://...).
            pool_size: Number of connections to maintain in the pool. Defaults to 10.
            max_overflow: Maximum number of connections to create beyond pool_size. Defaults to 10.
            echo: If True, log all SQL statements. Defaults to False.
        """
        self._engine = create_async_engine(
            url=database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide async database session with automatic transaction management.

        Automatically commits on successful completion and rolls back on exceptions.
        Should be used as an async context manager.

        Yields:
            AsyncSession: Active database session.

        Raises:
            Exception: Re-raises any exception that occurs during session usage after rollback.

        Example:
            async with db_client.session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
        """
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            await session.commit()

    async def dispose(self) -> None:
        """Close all connections in the pool.

        Should be called during application shutdown to ensure graceful cleanup
        of database connections.
        """
        await self._engine.dispose()
