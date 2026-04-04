"""Redis worker entry point.

Consumes tasks from a Redis queue and dispatches them
to domain-specific handlers with status tracking.
"""

import asyncio
import signal
import uuid

from src.configs.config import AppConfigs
from src.configs.log.logger import get_logger, setup_logger
from src.domains.task.app.constants import TaskStatus, TaskType
from src.domains.task.app.usecases.service import TaskService
from src.domains.task.app.workers.handler import TaskHandler
from src.domains.task.app.workers.registry import build_handler_registry
from src.domains.task.db.redis.repository import TaskQueueRepository
from src.infrastructure.containers.domain import DomainContainer
from src.infrastructure.db.redis.client import RedisClient
from src.schemas.task import TaskSchema, UpdateTaskSchema

settings = AppConfigs.init()

setup_logger(settings.logger.logging_config_file)
logger = get_logger(__name__)


def init_containers() -> DomainContainer:
    """Initialize and wire DI containers for the worker."""
    container = DomainContainer()
    container.config.from_dict(settings.model_dump())
    container.wire(packages=["src.domains"])
    return container


def _setup_stop_event() -> asyncio.Event:
    """Create an Event and bind SIGINT/SIGTERM to set it.

    Returns:
        Event that will be set when a shutdown signal is received.
    """
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_event.set)
    loop.add_signal_handler(signal.SIGTERM, stop_event.set)
    return stop_event


async def _shutdown(redis_client: RedisClient) -> None:
    """Close all external connections gracefully.

    Args:
        redis_client: Redis client to close.
    """
    await redis_client.close()
    logger.info("Worker shut down successfully")


async def _process_task(
    task_service: TaskService,
    task_executor: TaskHandler,
    task_id: uuid.UUID,
    task: TaskSchema,
) -> None:
    """Run a single task through its executor with status updates.

    Sets the task to ``IN_PROGRESS`` before execution.
    On success marks it ``COMPLETED``; on failure — ``FAILED``
    with the error message persisted in ``error_log``.

    Args:
        task_service: Service for persisting task status changes.
        task_executor: Domain executor that performs the actual work.
        task_id: Unique identifier of the task.
        task: Full task payload from the queue.
    """
    await task_service.update_task(
        task_id,
        UpdateTaskSchema(status=TaskStatus.IN_PROGRESS),
    )
    try:
        await task_executor.execute(task)
    except Exception as exc:
        logger.error("Task %s failed: %s", task_id, exc)
        await task_service.update_task(
            task_id,
            UpdateTaskSchema(status=TaskStatus.FAILED, error_log=str(exc)),
        )
        return

    await task_service.update_task(
        task_id,
        UpdateTaskSchema(status=TaskStatus.COMPLETED, progress=1.0),
    )


async def run_worker(
    redis_task_repository: TaskQueueRepository,
    task_service: TaskService,
    task_executor_registry: dict[TaskType, TaskHandler],
    stop_event: asyncio.Event,
) -> None:
    """Poll the Redis queue until a stop signal is received.

    On each iteration the worker blocks for up to
    ``settings.redis.timeout`` seconds waiting for a task.
    If no task arrives the loop re-checks the stop event.

    Args:
        redis_task_repository: Redis-backed task queue.
        task_service: Service for persisting task status changes.
        task_executor_registry: Mapping of task types to their executors.
        stop_event: Event set by SIGINT/SIGTERM to trigger shutdown.
    """
    logger.info("Worker started, waiting for tasks")

    while not stop_event.is_set():
        task = await redis_task_repository.dequeue(timeout=settings.redis.timeout)

        if task is None:
            continue

        task_executor = task_executor_registry.get(task.type)

        if task_executor is None:
            logger.error("No executor registered for task type: %s", task.type)
            await task_service.update_task(
                task.task_id,
                UpdateTaskSchema(
                    status=TaskStatus.FAILED,
                    error_log=f"No executor for task type {task.type.value}",
                ),
            )
        else:
            await _process_task(task_service, task_executor, task.task_id, task)

    logger.info("Stop signal received, exiting worker loop")


async def main() -> None:
    """Bootstrap the worker and enter the processing loop."""
    container = init_containers()

    redis_task_repository: TaskQueueRepository = container.task.redis_repository()  # type: ignore[operator]
    task_service: TaskService = container.task.task_service()  # type: ignore[operator]
    task_executor_registry = build_handler_registry(container)
    stop_event = _setup_stop_event()

    try:
        await run_worker(redis_task_repository, task_service, task_executor_registry, stop_event)
    except Exception as exc:
        logger.error("Unexpected worker error: %s", exc)
    finally:
        await _shutdown(redis_task_repository.redis_client)


if __name__ == "__main__":
    asyncio.run(main())
