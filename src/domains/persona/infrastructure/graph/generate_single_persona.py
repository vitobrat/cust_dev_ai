from typing import Any

from langgraph.graph import END, START

from src.configs.log.logger import get_logger
from src.domains.persona.infrastructure.graph.graph_utils import (
    get_demographic_attributes,
    get_segment_description,
    get_segment_name,
)
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.state_schemas import (
    GeneratePersonaInputData,
    GeneratePersonaSchema,
    GeneratePersonasOutputData,
    GeneratePersonasOutputSchema,
    PersonaSchema,
)
from src.infrastructure.graph.base_graph import BaseGraph


class GenerateSinglePersonaGraph(
    BaseGraph[
        GeneratePersonaInputData,
        GeneratePersonaSchema,
        GeneratePersonasOutputSchema,
        GeneratePersonasOutputData,
    ],
):

    _prompt_builder: PersonaPromptManager

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the graph with the necessary components."""
        super().__init__(
            state_schema=GeneratePersonaSchema,
            output_schema=GeneratePersonasOutputSchema,
            output_data_model=GeneratePersonasOutputData,
            **kwargs,
        )
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def _configurate_graph(self) -> None:  # noqa: WPS213
        self.add_node("generate_persona_attribute", self._generate_persona_attribute)
        self.add_node("generate_biography", self._generate_persona_biography)
        self.add_node("generate_experiences", self._generate_persona_experiences)
        self.add_node("format_output", self._format_output)

        self.add_edge(START, "generate_persona_attribute")

        self.add_edge("generate_persona_attribute", "generate_biography")
        self.add_edge("generate_persona_attribute", "generate_experiences")

        self.add_edge("generate_biography", "format_output")
        self.add_edge("generate_experiences", "format_output")

        self.add_edge("format_output", END)

    async def _generate_persona_attribute(self, state: GeneratePersonaSchema) -> GeneratePersonaSchema:
        """Create a demographic attribute person based on the input data."""
        segment_name = get_segment_name(state)
        segment_description = get_segment_description(state)

        prompt = self._prompt_builder.build_generate_persona_prompt(
            segment_name=segment_name,
            segment_description=segment_description,
        )

        response_structured = await self._llm_adapter.structured_ainvoke(
            prompt,
            DemographicAttributePersona,
        )

        return {
            "demographic_attributes": response_structured,
        }

    async def _generate_persona_biography(self, state: GeneratePersonaSchema) -> GeneratePersonaSchema:
        """Generate a biography for the persona based on the demographic attributes."""
        demographic_attributes = get_demographic_attributes(state)

        segment_description = get_segment_description(state)

        prompt = self._prompt_builder.build_generate_persona_biography_prompt(
            demographic_attributes=demographic_attributes.demographic_info,
            segment_description=segment_description,
        )

        response = await self._llm_adapter.ainvoke(prompt)

        return {
            "biography": response,
        }

    async def _generate_persona_experiences(self, state: GeneratePersonaSchema) -> GeneratePersonaSchema:
        """Generate the experiences of the persona with the problem based on the demographic attributes."""
        demographic_attributes = get_demographic_attributes(state)

        segment_description = get_segment_description(state)

        prompt = self._prompt_builder.build_generate_persona_experiences_prompt(
            demographic_attributes=demographic_attributes.demographic_info,
            segment_description=segment_description,
        )

        response = await self._llm_adapter.ainvoke(prompt)

        return {
            "experiences": response,
        }

    async def _format_output(self, state: GeneratePersonaSchema) -> GeneratePersonasOutputSchema:
        """
        Format the final output by combining demographic attributes, biography,
        and experiences into a structured persona.
        """
        demographic_attributes = get_demographic_attributes(state)

        persona = PersonaSchema(
            demographic_attributes=demographic_attributes,
            biography=state.get("biography") or "",
            experiences=state.get("experiences") or "",
        )

        return {
            "personas": [persona],
        }
