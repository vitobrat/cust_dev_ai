"""Handler registry for mapping task types to their handlers."""

from src.domains.task.app.constants import TaskType
from src.domains.task.app.workers.handler import TaskHandler
from src.infrastructure.containers.domain import DomainContainer


def build_handler_registry(
    container: DomainContainer,
) -> dict[TaskType, TaskHandler]:
    """Build a mapping of every ``TaskType`` to its handler instance.

    Handler instances are resolved from the DI container.

    Args:
        container: Fully wired domain container.

    Returns:
        Dictionary mapping each task type to its handler.
    """
    persona_handler = container.persona.persona_task_handler()  # type: ignore[operator]
    return {
        TaskType.PERSONAS_GENERATION: persona_handler,
        TaskType.SINGLE_PERSONA_GENERATION: persona_handler,
        TaskType.SUB_INTERVIEW_GENERATION: (
            container.sub_interview.sub_interview_generation_handler()  # type: ignore[operator]
        ),
        TaskType.REPORT_GENERATION: container.interview.report_generation_handler(),  # type: ignore[operator]
    }
