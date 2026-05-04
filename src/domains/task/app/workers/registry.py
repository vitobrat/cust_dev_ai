"""Handler registry for mapping task types to their handlers."""

from src.domains.task.app.constants import TaskType
from src.domains.task.app.workers.handler import TaskHandler
from src.infrastructure.containers.domain import DomainContainer


def build_handler_registry(
    container: DomainContainer,
) -> dict[TaskType, TaskHandler]:
    """Build a mapping of implemented ``TaskType`` values to handler instances.

    Handler instances are resolved from the DI container.

    Args:
        container: Fully wired domain container.

    Returns:
        Dictionary mapping each task type to its handler.
    """
    persona_handler = container.persona.persona_task_handler()  # type: ignore[operator]
    interview_handler = container.interview.interview_simulation_task_handler()  # type: ignore[operator]
    final_report_handler = container.interview.final_report_generation_task_handler()  # type: ignore[operator]
    return {
        TaskType.PERSONAS_PIPELINE: persona_handler,
        TaskType.PERSONAS_GENERATION: persona_handler,
        TaskType.SINGLE_PERSONA_GENERATION: persona_handler,
        TaskType.INTERVIEW_SIMULATION: interview_handler,
        TaskType.REPORT_GENERATION: final_report_handler,
    }
