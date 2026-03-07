"""Domain dependency injection container module.

This module defines dependency injection containers for domain-specific
components using the dependency-injector library. It organizes domain
services, repositories, and graphs with their dependencies.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from src.configs.config import AppConfigs
from src.domains.persona.db.postgres.repository import PersonaRepository
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
    """Dependency injection container for Persona domain components.

    This container manages all dependencies related to the Persona domain,
    including repositories, prompt managers, and LangGraph workflows.

    Attributes:
        config: Application configuration provider.
        infrastructure: Infrastructure container with shared services.
        personas_repository: Factory for PersonaRepository instances.
        prompt_builder: Singleton PersonaPromptManager for prompt templates.
        user_segment_search_graph: Factory for user segment search graph.
        generate_single_persona_graph: Factory for single persona generation graph.
        generate_personas_graph: Factory for batch persona generation graph.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    personas_repository: PersonaRepository = providers.Factory(
        PersonaRepository,
    )

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
    """Root domain dependency injection container.

    This container aggregates all domain-specific containers and provides
    a unified interface for accessing domain services across the application.

    Attributes:
        config: Application configuration provider.
        infrastructure: Infrastructure container with shared services.
        persona: Persona domain container with all persona-related components.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    persona: PersonaContainer = providers.Container(
        PersonaContainer,
        config=config,
        infrastructure=infrastructure,
    )
