"""Infrastructure dependency injection container module.

This module defines the dependency injection container for infrastructure-level
components such as database clients, LLM adapters, and observability handlers.
These components are shared across all domains.
"""

from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from src.configs.config import AppConfigs
from src.infrastructure.db.postgres.client import DatabaseClient
from src.infrastructure.llm.llm_adapter import LLMAdapter


class InfrastructureContainer(containers.DeclarativeContainer):
    """Dependency injection container for infrastructure components.

    This container manages shared infrastructure services including database
    connections, LLM clients, and observability tools. All providers are
    configured from the application configuration.

    Attributes:
        config: Application configuration provider.
        db_client: Singleton DatabaseClient for PostgreSQL connections.
        llm: Singleton ChatOpenAI instance for language model interactions.
        llm_adapter: Factory for LLMAdapter wrapping the LLM client.
        langfuse_client: Singleton Langfuse client for observability.
        langfuse_handler: Factory for Langfuse callback handlers.
    """

    config: AppConfigs = providers.Configuration()

    db_client: DatabaseClient = providers.Singleton(
        DatabaseClient,
        database_url=config.postgres.database_url,
        pool_size=config.postgres.pool_size,
        max_overflow=config.postgres.max_overflow,
        echo=config.postgres.echo,
    )

    llm: ChatOpenAI = providers.Singleton(
        ChatOpenAI,
        model_name=config.llm.model_name,
        api_key=config.llm.api_key,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        base_url=config.llm.base_llm_url,
    )

    llm_adapter: LLMAdapter = providers.Factory(
        LLMAdapter,
        llm=llm,
    )

    langfuse_client = providers.Singleton(get_client)

    langfuse_handler = providers.Factory(CallbackHandler)
