"""Persona generation task handler for the Redis worker."""

from src.configs.log.logger import get_logger
from src.domains.persona.app.usecases.service import PersonaService
from src.domains.persona.schemas.generate_persona.state_schemas import (
    GeneratePersonasInputData as GraphInputData,
)
from src.schemas.persona import GeneratePersonasInputData
from src.schemas.task import TaskSchema


class PersonaGenerationTaskHandler:
    """Handle ``PERSONA_GENERATION`` tasks.

    Validates that ``input_params`` is a ``GeneratePersonasInputData``
    instance and delegates to :pymeth:`PersonaService.generate_persona`.

    Attributes:
        _persona_service: Service executing the persona generation workflow.
    """

    def __init__(self, persona_service: PersonaService) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._persona_service = persona_service

    async def execute(self, task: TaskSchema) -> None:
        """Execute persona generation for the given task.

        Args:
            task: Dequeued task with ``GeneratePersonasInputData`` payload.

        Raises:
            TypeError: If ``task.input_params`` has an unexpected type.
        """
        input_params = task.input_params

        if not isinstance(input_params, GeneratePersonasInputData):
            raise TypeError(
                f"Expected GeneratePersonasInputData, got {type(input_params).__name__}",
            )

        await self._persona_service.generate_persona(
            interview_id=input_params.interview_id,
            generate_persona_input=GraphInputData(
                segment_name=input_params.segment_name,
                segment_description=input_params.segment_description,
                person_count=input_params.person_count,
            ),
        )
