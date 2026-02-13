from __future__ import annotations

from dependency_injector import containers, providers

from src.configs.config import AppConfigs
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

    graph: UserSegmentSearchGraph = providers.Factory(
        UserSegmentSearchGraph,
        llm_adapter=infrastructure.llm_adapter,
        prompt_builder=prompt_builder,
        recursion_limit=config.persona.recursion_limit,
    )


class DomainContainer(containers.DeclarativeContainer):
    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    persona: PersonaContainer = providers.Container(
        PersonaContainer,
        config=config,
        infrastructure=infrastructure,
    )
