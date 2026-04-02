"""Pytest fixtures for TaskQueueRepository unit tests."""

from __future__ import annotations

import uuid
from typing import Any, Generator
from unittest.mock import AsyncMock, patch

import pytest

from src.domains.task.app.constants import TaskStatus, TaskType
from src.domains.task.db.redis.repository import TaskQueueRepository
from src.infrastructure.db.redis.client import RedisClient
from src.schemas.task import TaskSchema


@pytest.fixture
def mock_redis_client() -> Generator[RedisClient, Any, Any]:
    """Provide a RedisClient with mocked underlying Redis connection."""
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        yield RedisClient(redis_url="redis://:test@localhost:6379/0")


@pytest.fixture
def task_queue_repository(mock_redis_client: Any) -> Any:
    """Provide a TaskQueueRepository backed by the mocked RedisClient."""
    return TaskQueueRepository(mock_redis_client)


@pytest.fixture
def sample_task() -> TaskSchema:
    """Provide a valid TaskSchema instance for tests."""
    return TaskSchema(
        task_id=uuid.uuid4(),
        type=TaskType.PERSONA_GENERATION,
        status=TaskStatus.PENDING,
        progress=0,
        error_log=None,
        input_params={"segment": "developers"},
        user_id=uuid.uuid4(),
    )
