from typing import Any, Dict

from langgraph.graph import END, START

from src.configs.log.logger import get_logger
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.generate_persona import (
    DemographicAttributePersona,
    GeneratePersonaSchema,
    PersonaSchema,
)
from src.infrastructure.graph.base_graph import BaseGraph


class GenerateSinglePersona(BaseGraph):

    _prompt_builder: PersonaPromptManager

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the graph with the necessary components."""
        super().__init__(
            state_schema=GeneratePersonaSchema,
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

    async def _generate_persona_attribute(self, state: GeneratePersonaSchema) -> Dict[str, Any]:
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

        response_structured: DemographicAttributePersona = await self._llm_adapter.structured_ainvoke(
            prompt,
            DemographicAttributePersona,
        )

        return {
            "demographic_attributes": response_structured,
        }

    async def _generate_persona_biography(self, state: GeneratePersonaSchema) -> Dict[str, Any]:
        """Generate a biography for the persona based on the demographic attributes."""
        try:
            demographic_attributes = state["demographic_attributes"]
        except KeyError as error:
            self._logger.error(f"Demographic attributes not found in persona: {error}")
            raise ValueError("Demographic attributes are required in persona to generate biography.")

        if not isinstance(demographic_attributes, DemographicAttributePersona):
            self._logger.error(
                f"Demographic attributes is not of type DemographicAttributePersona: {type(demographic_attributes)}",
            )
            raise ValueError(
                "Demographic attributes must be of type DemographicAttributePersona to generate biography.",
            )

        prompt = self._prompt_builder.build_generate_persona_biography_prompt(
            demographic_attributes=demographic_attributes.demographic_info,
        )

        response = await self._llm_adapter.ainvoke(prompt)

        return {
            "biography": response,
        }

    async def _generate_persona_experiences(self, state: GeneratePersonaSchema) -> Dict[str, Any]:
        """Generate the experiences of the persona with the problem based on the demographic attributes."""
        try:
            demographic_attributes = state["demographic_attributes"]
        except KeyError as error:
            self._logger.error(f"Demographic attributes not found in persona: {error}")
            raise ValueError("Demographic attributes are required in persona to generate experiences.")

        try:
            segment_name = state["input_data"].segment_name
        except KeyError as key_error:
            self._logger.error(f"Segment_name not found in input_data: {key_error}")
            raise ValueError("Segment_name is required in input_data to generate a demographic attribute person.")

        if not isinstance(demographic_attributes, DemographicAttributePersona):
            self._logger.error(
                f"Demographic attributes is not of type DemographicAttributePersona: {type(demographic_attributes)}",
            )
            raise ValueError(
                "Demographic attributes must be of type DemographicAttributePersona to generate experiences.",
            )

        prompt = self._prompt_builder.build_generate_persona_experiences_prompt(
            demographic_attributes=demographic_attributes.demographic_info,
            segment_description=segment_name,
        )

        response = await self._llm_adapter.ainvoke(prompt)

        return {
            "experiences": response,
        }

    async def _format_output(self, state: GeneratePersonaSchema) -> Dict[str, Any]:
        """
        Format the final output by combining demographic attributes, biography,
        and experiences into a structured persona.
        """
        try:
            demographic_attributes = state["demographic_attributes"]
        except KeyError as error:
            self._logger.error(f"Demographic attributes not found in persona: {error}")
            raise ValueError("Demographic attributes are required in persona to format output.")

        persona = PersonaSchema(
            demographic_attributes=demographic_attributes,
            biography=state.get("biography", ""),
            experiences=state.get("experiences", ""),
        )

        return {
            "personas": [persona],
        }
