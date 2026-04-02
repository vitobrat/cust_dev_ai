"""Domain dependency injection container module.

This module defines dependency injection containers for domain-specific
components using the dependency-injector library. It organizes domain
services, repositories, and graphs with their dependencies.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from src.configs.config import AppConfigs
from src.domains.interview.app.usecases.service import InterviewService
from src.domains.interview.db.postgres.repository import InterviewRepository
from src.domains.persona.app.usecases.service import PersonaService
from src.domains.persona.db.postgres.repository import PersonaRepository
from src.domains.persona.infrastructure.graph.generate_personas import (
    GeneratePersonasGraph,
)
from src.domains.persona.infrastructure.graph.generate_single_persona import (
    GenerateSinglePersonaGraph,
)
from src.domains.persona.infrastructure.graph.user_segment_search import (
    UserSegmentSearchGraph,
)
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.sub_interview.app.usecases.service import SubInterviewService
from src.domains.sub_interview.db.postgres.repository import (
    SubInterviewRepository,
)
from src.domains.task.app.usecases.service import TaskService
from src.domains.task.db.postgres.repository import TaskRepository
from src.domains.user.app.usecases.service import UserService
from src.domains.user.db.postgres.repository import UserRepository
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
        persona_service: Factory for PersonaService instances.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    personas_repository: PersonaRepository = providers.Factory(
        PersonaRepository,
        db_client=infrastructure.db_client,
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

    generate_single_persona_graph: GenerateSinglePersonaGraph = providers.Factory(
        GenerateSinglePersonaGraph,
        prompt_builder=prompt_builder,
        llm_adapter=infrastructure.llm_adapter,
        langfuse_handler=infrastructure.langfuse_handler,
    )

    generate_personas_graph: GeneratePersonasGraph = providers.Factory(
        GeneratePersonasGraph,
        prompt_builder=prompt_builder,
        llm_adapter=infrastructure.llm_adapter,
        sub_graph=generate_single_persona_graph,
        langfuse_handler=infrastructure.langfuse_handler,
    )

    persona_service: PersonaService = providers.Factory(
        PersonaService,
        generate_personas_graph=generate_personas_graph,
        user_segment_search_graph=user_segment_search_graph,
        personas_repository=personas_repository,
    )


class InterviewContainer(containers.DeclarativeContainer):
    """Dependency injection container for Interview domain components.

    This container manages all dependencies related to the Interview domain,
    including the repository and service layer.

    Attributes:
        interviews_repository: Factory for InterviewRepository instances.
        interview_service: Factory for InterviewService instances.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    interviews_repository: InterviewRepository = providers.Factory(
        InterviewRepository,
        db_client=infrastructure.db_client,
    )

    interview_service: InterviewService = providers.Factory(
        InterviewService,
        interviews_repository=interviews_repository,
    )


class SubInterviewContainer(containers.DeclarativeContainer):
    """Dependency injection container for SubInterview domain components.

    Manages the repository and service layer for sub-interview entities.

    Attributes:
        sub_interviews_repository: Factory for SubInterviewRepository instances.
        sub_interview_service: Factory for SubInterviewService instances.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    sub_interviews_repository: SubInterviewRepository = providers.Factory(
        SubInterviewRepository,
        db_client=infrastructure.db_client,
    )

    sub_interview_service: SubInterviewService = providers.Factory(
        SubInterviewService,
        sub_interviews_repository=sub_interviews_repository,
    )


class TaskContainer(containers.DeclarativeContainer):
    """Dependency injection container for Task domain components.

    Manages the repository and service layer for task entities.

    Attributes:
        tasks_repository: Factory for TaskRepository instances.
        task_service: Factory for TaskService instances.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    tasks_repository: TaskRepository = providers.Factory(
        TaskRepository,
        db_client=infrastructure.db_client,
    )

    task_service: TaskService = providers.Factory(
        TaskService,
        tasks_repository=tasks_repository,
    )


class UserContainer(containers.DeclarativeContainer):
    """Dependency injection container for User domain components.

    Manages the repository and service layer for user entities.

    Attributes:
        users_repository: Factory for UserRepository instances.
        user_service: Factory for UserService instances.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    users_repository: UserRepository = providers.Factory(
        UserRepository,
        db_client=infrastructure.db_client,
    )

    user_service: UserService = providers.Factory(
        UserService,
        users_repository=users_repository,
    )


class DomainContainer(containers.DeclarativeContainer):
    """Root domain dependency injection container.

    This container aggregates all domain-specific containers and provides
    a unified interface for accessing domain services across the application.

    Attributes:
        config: Application configuration provider.
        infrastructure: Infrastructure container with shared services.
        persona: Persona domain container with all persona-related components.
        interview: Interview domain container with all interview-related components.
        sub_interview: SubInterview domain container with all sub-interview-related components.
        task: Task domain container with all task-related components.
        user: User domain container with all user-related components.
    """

    config: AppConfigs = providers.Configuration()
    infrastructure: InfrastructureContainer = providers.Container(
        InfrastructureContainer,
        config=config,
    )

    persona: PersonaContainer = providers.Container(
        PersonaContainer,
        config=config,
        infrastructure=infrastructure,
    )

    interview: InterviewContainer = providers.Container(
        InterviewContainer,
        infrastructure=infrastructure,
    )

    sub_interview: SubInterviewContainer = providers.Container(
        SubInterviewContainer,
        infrastructure=infrastructure,
    )

    task: TaskContainer = providers.Container(
        TaskContainer,
        infrastructure=infrastructure,
    )

    user: UserContainer = providers.Container(
        UserContainer,
        config=config,
        infrastructure=infrastructure,
    )
