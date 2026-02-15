from __future__ import annotations

from dependency_injector import containers, providers

from src.configs.config import AppConfigs
from src.domains.persona.infrastructure.graph.generate_personas import (
    GeneratePersonas,
)
from src.domains.persona.infrastructure.graph.generate_single_persona import (
    GenerateSinglePersona,
)
from src.domains.persona.infrastructure.graph.user_segment_search import (
    UserSegmentSearchGraph,
)
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.infrastructure.containers.infrastructure import InfrastructureContainer


class PersonaContainer(containers.DeclarativeContainer):
    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    prompt_builder: PersonaPromptManager = providers.Singleton(
        PersonaPromptManager,
        prompts_dir=config.persona.prompts_dir,
    )

    user_segment_search_graph: UserSegmentSearchGraph = providers.Factory(
        UserSegmentSearchGraph,
        prompt_builder=prompt_builder,
        llm_adapter=infrastructure.llm_adapter,
        recursion_limit=config.persona.recursion_limit,
        langfuse_handler=infrastructure.langfuse_handler,
    )

    generate_single_persona_graph: GenerateSinglePersona = providers.Factory(
        GenerateSinglePersona,
        prompt_builder=prompt_builder,
        llm_adapter=infrastructure.llm_adapter,
        langfuse_handler=infrastructure.langfuse_handler,
    )

    generate_personas_graph: GeneratePersonas = providers.Factory(
        GeneratePersonas,
        prompt_builder=prompt_builder,
        llm_adapter=infrastructure.llm_adapter,
        sub_graph=generate_single_persona_graph,
        langfuse_handler=infrastructure.langfuse_handler,
    )


class DomainContainer(containers.DeclarativeContainer):
    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    persona: PersonaContainer = providers.Container(
        PersonaContainer,
        config=config,
        infrastructure=infrastructure,
    )
