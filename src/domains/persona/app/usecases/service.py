"""Business logic service for the Persona domain."""

import uuid

from src.configs.log.logger import get_logger
from src.domains.persona.db.postgres.repository import PersonaRepository
from src.domains.persona.exceptions import (
    PersonaDeletionFailed,
    PersonaGetFailed,
    PersonaUpdationFailed,
)
from src.domains.persona.infrastructure.graph.generate_personas import (
    GeneratePersonasGraph,
)
from src.domains.persona.infrastructure.graph.generate_single_persona import (
    GenerateSinglePersonaGraph,
)
from src.domains.persona.infrastructure.graph.user_segment_search import (
    UserSegmentSearchGraph,
)
from src.domains.persona.schemas.generate_persona.state_schemas import (
    GeneratePersonasInputData,
    PersonaSchema,
)
from src.schemas.persona import (
    CreatePersonaSchema,
    GenerateSinglePersonaInputData,
    PersonaRelEntitySchema,
    UpdatePersonasSchema,
)


class PersonaService:
    """Service layer for persona business logic.

    Encapsulates CRUD operations and graph-based generation workflows for personas.

    Attributes:
        _generate_personas_graph: Graph for batch persona generation from interview data.
        _generate_single_persona_graph: Graph for single persona generation.
        _user_segment_search_graph: Graph for user segment discovery.
        _personas_repository: Repository for persona persistence operations.
    """

    def __init__(
        self,
        generate_personas_graph: GeneratePersonasGraph,
        generate_single_persona_graph: GenerateSinglePersonaGraph,
        user_segment_search_graph: UserSegmentSearchGraph,
        personas_repository: PersonaRepository,
    ) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._generate_personas_graph = generate_personas_graph
        self._generate_single_persona_graph = generate_single_persona_graph
        self._user_segment_search_graph = user_segment_search_graph
        self._personas_repository = personas_repository

    async def generate_single_persona(
        self,
        interview_id: uuid.UUID,
        generate_single_persona_input: GenerateSinglePersonaInputData,
    ) -> None:
        """Generate a single persona via LangGraph and persist it.

        Args:
            interview_id: Interview to associate the generated persona with.
            generate_single_persona_input: Validated input for the single persona graph.
        """
        generate_single_persona_response = await self._generate_single_persona_graph.process(
            generate_single_persona_input,
        )
        await self._persist_personas(interview_id, generate_single_persona_response.personas)

    async def generate_personas(
        self,
        interview_id: uuid.UUID,
        generate_personas_input: GeneratePersonasInputData,
    ) -> None:
        """Generate personas via LangGraph and persist them.

        Args:
            interview_id: Interview to associate generated personas with.
            generate_personas_input: Validated input for the batch generation graph.
        """
        generate_personas_response = await self._generate_personas_graph.process(
            generate_personas_input,
        )
        await self._persist_personas(interview_id, generate_personas_response.personas)

    async def create_persona(self, create_persona_data: CreatePersonaSchema) -> PersonaRelEntitySchema:
        """Persist a new persona entity.

        Args:
            create_persona_data: Validated creation payload.

        Returns:
            Newly created persona entity with generated ID and timestamps.
        """
        return await self._personas_repository.create(create_persona_data)

    async def get_persona(self, persona_id: uuid.UUID) -> PersonaRelEntitySchema:
        """Retrieve a single persona by its identifier.

        Args:
            persona_id: UUID of the persona to retrieve.

        Returns:
            Persona entity if found.

        Raises:
            PersonaGetFailed: If no persona with the given ID exists.
        """
        persona = await self._personas_repository.get_by_id(persona_id)

        if persona is None:
            self._logger.error("Persona not found: %s", persona_id)
            raise PersonaGetFailed(f"Persona with id={persona_id} does not exist.")

        return persona

    async def get_personas(self, limit: int = 10, offset: int = 0) -> list[PersonaRelEntitySchema]:
        """Retrieve a paginated list of personas.

        Args:
            limit: Maximum number of records to return. Defaults to 10.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of persona entities (may be empty).
        """
        return await self._personas_repository.get_all(limit, offset)

    async def count_personas(self) -> int:
        """Return the total number of stored personas.

        Returns:
            Integer count of persona records.
        """
        return await self._personas_repository.get_count()

    async def update_persona(
        self,
        persona_id: uuid.UUID,
        update_persona_data: UpdatePersonasSchema,
    ) -> PersonaRelEntitySchema:
        """Apply a partial update to an existing persona.

        Args:
            persona_id: UUID of the persona to update.
            update_persona_data: Partial schema; only set fields are applied.

        Returns:
            Updated persona entity.

        Raises:
            PersonaUpdationFailed: If no persona with the given ID exists.
        """
        updated_persona = await self._personas_repository.update_by_id(persona_id, update_persona_data)

        if updated_persona is None:
            self._logger.error("Persona not found for update: %s", persona_id)
            raise PersonaUpdationFailed(f"Persona with id={persona_id} does not exist.")

        return updated_persona

    async def delete_persona(self, persona_id: uuid.UUID) -> None:
        """Delete a persona by its identifier.

        Args:
            persona_id: UUID of the persona to delete.

        Raises:
            PersonaDeletionFailed: If no persona with the given ID exists.
        """
        deleted_id = await self._personas_repository.delete_by_id(persona_id)

        if deleted_id is None:
            self._logger.error("Persona not found for deletion: %s", persona_id)
            raise PersonaDeletionFailed(f"Persona with id={persona_id} does not exist.")

    async def _persist_personas(
        self,
        interview_id: uuid.UUID,
        personas: list[PersonaSchema],
    ) -> None:
        """Save generated personas to the database.

        Args:
            interview_id: Interview to link each persona to.
            personas: Persona schemas produced by a generation graph.
        """
        for persona in personas:
            await self._personas_repository.create(
                CreatePersonaSchema(
                    interview_id=interview_id,
                    demographic_state=persona.demographic_attributes,
                    bio_description=persona.biography,
                    is_verified=False,
                ),
            )
