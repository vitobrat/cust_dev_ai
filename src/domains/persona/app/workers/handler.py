"""Persona domain task handler for the Redis worker."""

from typing import Awaitable, Callable

from src.configs.log.logger import get_logger
from src.domains.persona.app.usecases.service import PersonaService
from src.domains.task.app.constants import TaskType
from src.schemas.persona import (
    GeneratePersonasTaskInputData,
    GenerateSinglePersonaTaskInputData,
    PersonasPipelineTaskInputData,
)
from src.schemas.task import TaskSchema

_TaskExecutor = Callable[[TaskSchema], Awaitable[None]]


class PersonaTaskHandler:
    """Route persona-related tasks to the appropriate service method.

    Maintains an internal dispatch table that maps each persona ``TaskType``
    to a private handler method.  New task types are added by writing
    a ``_handle_*`` method and registering it in ``_dispatch``.

    Attributes:
        _persona_service: Service that executes persona generation workflows.
    """

    def __init__(self, persona_service: PersonaService) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._persona_service = persona_service
        self._dispatch: dict[TaskType, _TaskExecutor] = {
            TaskType.PERSONAS_PIPELINE: self._handle_personas_pipeline,
            TaskType.SINGLE_PERSONA_GENERATION: self._handle_single_persona,
            TaskType.PERSONAS_GENERATION: self._handle_personas,
        }

    async def execute(self, task: TaskSchema) -> None:
        """Execute the persona task by dispatching to the correct handler.

        Args:
            task: Dequeued task payload.

        Raises:
            ValueError: If ``task.type`` is not registered in the dispatch table.
            TypeError: If ``task.input_params`` has an unexpected type.
        """
        task_executor = self._dispatch.get(task.type)
        if task_executor is None:
            raise ValueError(f"Unsupported persona task type: {task.type}")
        await task_executor(task)

    async def _handle_personas_pipeline(self, task: TaskSchema) -> None:
        """Validate input and delegate to full persona generation pipeline.

        Runs user segment search followed by batch persona generation.

        Args:
            task: Task with ``PersonasPipelineTaskInputData`` payload.

        Raises:
            TypeError: If ``task.input_params`` is not ``PersonasPipelineTaskInputData``.
        """
        input_params = task.input_params
        if not isinstance(input_params, PersonasPipelineTaskInputData):
            raise TypeError(
                f"Expected PersonasPipelineTaskInputData, got {type(input_params).__name__}",
            )

        await self._persona_service.generate_personas_pipeline(
            interview_id=input_params.interview_id,
            person_count=input_params.person_count,
            generate_personas_pipeline_input=input_params,
        )

    async def _handle_single_persona(self, task: TaskSchema) -> None:
        """Validate input and delegate to single persona generation.

        Args:
            task: Task with ``GenerateSinglePersonaInputData`` payload.

        Raises:
            TypeError: If ``task.input_params`` is not ``GenerateSinglePersonaInputData``.
        """
        input_params = task.input_params
        if not isinstance(input_params, GenerateSinglePersonaTaskInputData):
            raise TypeError(
                f"Expected GenerateSinglePersonaInputData, got {type(input_params).__name__}",
            )

        await self._persona_service.generate_single_persona(
            interview_id=input_params.interview_id,
            generate_single_persona_input=input_params,
        )

    async def _handle_personas(self, task: TaskSchema) -> None:
        """Validate input and delegate to batch persona generation.

        Args:
            task: Task with ``GeneratePersonasInputData`` payload.

        Raises:
            TypeError: If ``task.input_params`` is not ``GeneratePersonasInputData``.
        """
        input_params = task.input_params
        if not isinstance(input_params, GeneratePersonasTaskInputData):
            raise TypeError(
                f"Expected GeneratePersonasInputData, got {type(input_params).__name__}",
            )

        await self._persona_service.generate_personas(
            interview_id=input_params.interview_id,
            generate_personas_input=input_params,
        )
