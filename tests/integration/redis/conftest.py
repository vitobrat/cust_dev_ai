"""Pytest fixtures for Redis integration tests."""

import pytest

from src.domains.task.db.redis.repository import TaskQueueRepository
from src.infrastructure.db.redis.client import RedisClient


@pytest.fixture
def task_queue_repository(redis_client: RedisClient) -> TaskQueueRepository:
    """Provide a TaskQueueRepository backed by the test RedisClient.

    Args:
        redis_client: Test RedisClient connected to the testcontainer.

    Returns:
        TaskQueueRepository instance for integration testing.
    """
    return TaskQueueRepository(redis_client)
