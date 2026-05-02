"""Unit tests for Redis worker task dispatch behavior."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from src.domains.task.app.constants import TaskStatus, TaskType
from src.domains.task.app.workers.registry import build_handler_registry
from src.redis_worker import _process_task, run_worker
from src.schemas.task import TaskSchema, UpdateTaskSchema

_STARTED_PROGRESS = 0.1


class _StopWorkerOnUpdate:
    """Stop the worker after task status update."""

    def __init__(self, stop_event: asyncio.Event) -> None:
        self._stop_event = stop_event

    def __call__(self, task_id: uuid.UUID, update_data: UpdateTaskSchema) -> None:
        self._stop_event.set()


async def test_registry_registers_only_implemented_task_types() -> None:
    """Incomplete task types must not be registered as executable handlers."""
    persona_task_handler = MagicMock()
    interview_task_handler = MagicMock()
    container = MagicMock()
    container.persona.persona_task_handler.return_value = persona_task_handler
    container.interview.interview_simulation_task_handler.return_value = interview_task_handler

    registry = build_handler_registry(container)

    assert registry == {
        TaskType.PERSONAS_PIPELINE: persona_task_handler,
        TaskType.PERSONAS_GENERATION: persona_task_handler,
        TaskType.SINGLE_PERSONA_GENERATION: persona_task_handler,
        TaskType.INTERVIEW_SIMULATION: interview_task_handler,
    }


async def test_worker_marks_unregistered_task_type_failed(sample_task: TaskSchema) -> None:
    """Unregistered task types must fail through the controlled worker path."""
    stop_event = asyncio.Event()
    unsupported_task = sample_task.model_copy(update={"type": TaskType.REPORT_GENERATION})
    redis_task_repository = MagicMock()
    redis_task_repository.dequeue = AsyncMock(return_value=unsupported_task)
    task_service = MagicMock()
    task_service.update_task = AsyncMock(side_effect=_StopWorkerOnUpdate(stop_event))

    await run_worker(
        redis_task_repository=redis_task_repository,
        task_service=task_service,
        task_executor_registry={},
        stop_event=stop_event,
    )

    update_data = task_service.update_task.call_args.args[1]
    assert update_data.status == TaskStatus.FAILED
    assert update_data.error_log == "No executor for task type report_generation"


async def test_process_task_sets_visible_started_progress(sample_task: TaskSchema) -> None:
    """Starting a task must persist non-zero progress before running the executor."""
    task_service = MagicMock()
    task_service.update_task = AsyncMock()
    task_executor = MagicMock()
    task_executor.execute = AsyncMock()

    await _process_task(task_service, task_executor, sample_task.task_id, sample_task)

    update_calls = task_service.update_task.await_args_list
    first_call = update_calls[0]
    final_call = update_calls[-1]
    first_update = first_call.args[1]
    final_update = final_call.args[1]
    assert first_update.status == TaskStatus.IN_PROGRESS
    assert first_update.progress == _STARTED_PROGRESS
    assert final_update.status == TaskStatus.COMPLETED
    assert final_update.progress == 1
