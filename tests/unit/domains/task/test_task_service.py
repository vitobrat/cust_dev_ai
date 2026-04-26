"""Unit tests for TaskService registration behavior."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domains.task.app.constants import TaskStatus, TaskType
from src.domains.task.app.usecases.service import TaskService
from src.domains.task.exceptions import TaskQueueError
from src.schemas.persona import GeneratePersonasTaskInputData


def _task_input(interview_id: uuid.UUID) -> GeneratePersonasTaskInputData:
    """Build a valid batch persona task input."""
    return GeneratePersonasTaskInputData(
        interview_id=interview_id,
        segment_name="developers",
        segment_description="Software developers",
        person_count=3,
    )


async def test_register_generate_personas_task_creates_and_enqueues_task() -> None:
    """Registering a persona task must persist it and enqueue the Redis payload."""
    task_id = uuid.uuid4()
    user_id = uuid.uuid4()
    tasks_repository = MagicMock()
    tasks_repository.create = AsyncMock(return_value=SimpleNamespace(id=task_id, type=TaskType.PERSONAS_GENERATION))
    redis_task_repository = MagicMock()
    redis_task_repository.enqueue = AsyncMock(return_value=1)
    task_service = TaskService(tasks_repository, redis_task_repository)

    await task_service.register_generate_personas_task(user_id, _task_input(uuid.uuid4()))

    queued_task = redis_task_repository.enqueue.call_args.args[0]
    assert tasks_repository.create.await_count == 1
    assert queued_task.task_id == task_id
    assert queued_task.user_id == user_id
    assert queued_task.type == TaskType.PERSONAS_GENERATION


async def test_register_generate_personas_task_marks_failed_when_enqueue_fails() -> None:
    """Queue failures must mark the persisted task as failed before re-raising."""
    task_id = uuid.uuid4()
    user_id = uuid.uuid4()
    tasks_repository = MagicMock()
    tasks_repository.create = AsyncMock(return_value=SimpleNamespace(id=task_id, type=TaskType.PERSONAS_GENERATION))
    tasks_repository.update_by_id = AsyncMock()
    redis_task_repository = MagicMock()
    redis_task_repository.enqueue = AsyncMock(side_effect=TaskQueueError("redis down"))
    task_service = TaskService(tasks_repository, redis_task_repository)

    with pytest.raises(TaskQueueError):
        await task_service.register_generate_personas_task(user_id, _task_input(uuid.uuid4()))

    update_data = tasks_repository.update_by_id.call_args.args[1]
    assert tasks_repository.update_by_id.call_args.args[0] == task_id
    assert update_data.status == TaskStatus.FAILED
