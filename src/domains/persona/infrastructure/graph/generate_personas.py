from typing import Any, List

from langgraph.graph import END, START
from langgraph.types import Send

from src.configs.log.logger import get_logger
from src.domains.persona.infrastructure.graph.generate_single_persona import (
    GenerateSinglePersona,
)
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.generate_persona import (
    BaseInputData,
    GeneratePersonasSchema,
    PersonaSchema,
)
from src.infrastructure.graph.base_graph import BaseGraph


class GeneratePersonas(BaseGraph):

    _prompt_builder: PersonaPromptManager

    def __init__(self, sub_graph: GenerateSinglePersona, **kwargs: Any) -> None:
        """Initialize the graph with the necessary components."""
        super().__init__(
            state_schema=GeneratePersonasSchema,
            **kwargs,
        )
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._sub_graph_generate_single_persona = sub_graph

    def _configurate_graph(self) -> None:
        self.add_node("generate_single_persona", self._sub_graph_generate_single_persona.graph)

        self.add_conditional_edges(START, self._map_personas, ["generate_single_persona"])
        self.add_edge("generate_single_persona", END)

    async def _map_personas(self, state: GeneratePersonasSchema) -> List[Send]:

        try:
            count = state["input_data"].person_count
        except KeyError:
            count = 1  # Default to 1 if person_count is not provided
            self._logger.warning("Person_count not found in input_data, defaulting to 1.")

        try:
            segment_name = state["input_data"].segment_name
        except KeyError as key_error:
            self._logger.error(f"Segment_name not found in input_data: {key_error}")
            raise ValueError("Segment_name is required in input_data to generate personas.")

        try:
            segment_description = state["input_data"].segment_description
        except KeyError as key_error:
            self._logger.error(f"Segment_description not found in input_data: {key_error}")
            raise ValueError("Segment_description is required in input_data to generate personas.")

        return [
            Send(
                "generate_single_persona",
                PersonaSchema(
                    input_data=BaseInputData(segment_name=segment_name, segment_description=segment_description),
                ),
            )
            for _ in range(count)
        ]
