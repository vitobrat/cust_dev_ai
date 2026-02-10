from typing import Any, Dict, List

from langgraph.graph import END, START
from langgraph.types import Send

from src.configs.log.logger import get_logger
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.demographic_attribute_person import (
    DemographicAttributePerson,
    GenerateDemographicAttributePersonSchema,
)
from src.infrastructure.graph.base_graph import BaseGraph


class GenerateDemographicAttributePerson(BaseGraph):

    _prompt_builder: PersonaPromptManager

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the graph with the necessary components."""
        super().__init__(
            state_schema=GenerateDemographicAttributePersonSchema,
            **kwargs,
        )
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def _configurate_graph(self) -> None:
        self.add_node("generate_persona", self._generate_single_persona)

        self.add_conditional_edges(START, self._map_personas, ["generate_persona"])
        self.add_edge("generate_persona", END)

    async def _map_personas(self, state: GenerateDemographicAttributePersonSchema) -> List[Send]:

        try:
            count = state["input_data"].person_count
        except KeyError:
            count = 1  # Default to 1 if person_count is not provided
            self._logger.warning("Person_count not found in input_data, defaulting to 1.")

        return [Send("create_demographic_attribute_person", state) for _ in range(count)]

    async def _generate_single_persona(self, state: GenerateDemographicAttributePersonSchema) -> Dict[str, Any]:
        """Create a demographic attribute person based on the input data."""
        try:
            segment_name = state["input_data"].segment_name
        except KeyError as key_error:
            self._logger.error(f"Segment_name not found in input_data: {key_error}")
            raise ValueError("Segment_name is required in input_data to generate a demographic attribute person.")

        try:
            segment_description = state["input_data"].segment_description
        except KeyError as key_error:
            self._logger.error(f"Segment_description not found in input_data: {key_error}")
            raise ValueError(
                "Segment_description is required in input_data to generate a demographic attribute person.",
            )

        prompt = self._prompt_builder.build_generate_persona_prompt(
            segment_name=segment_name,
            segment_description=segment_description,
        )

        response_structured: DemographicAttributePerson = await self._llm_adapter.structured_ainvoke(
            prompt,
            DemographicAttributePerson,
        )

        return {"demographic_attributes": [response_structured]}
