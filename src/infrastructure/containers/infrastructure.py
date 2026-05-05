"""Infrastructure dependency injection container module.

This module defines the dependency injection container for infrastructure-level
components such as database clients, LLM adapters, and observability handlers.
These components are shared across all domains.
"""

from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from src.configs.config import AppConfigs, RabbitMQConfigs
from src.infrastructure.db.postgres.client import DatabaseClient
from src.infrastructure.db.redis.client import RedisClient
from src.infrastructure.db.redis.repository import BaseRedisRepository
from src.infrastructure.llm.llm_adapter import LLMAdapter
from src.infrastructure.object_storage.client import MinioObjectStorageClient
from src.infrastructure.rabbitmq.client import RabbitMQClient


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
        object_storage_client: Singleton Minio-backed object storage client.
    """

    config: AppConfigs = providers.Configuration()

    db_client: DatabaseClient = providers.Singleton(
        DatabaseClient,
        database_url=config.postgres.database_url,
        pool_size=config.postgres.pool_size,
        max_overflow=config.postgres.max_overflow,
        echo=config.postgres.echo,
    )

    rabbitmq_client = providers.Singleton(
        RabbitMQClient,
        configs=providers.Singleton(
            RabbitMQConfigs,
            host=config.rabbitmq.host,
            port=config.rabbitmq.port,
            vhost=config.rabbitmq.vhost,
            user=config.rabbitmq.user,
            password=config.rabbitmq.password,
        ),
    )

    redis_client: RedisClient = providers.Singleton(
        RedisClient,
        redis_url=config.redis.redis_url,
        max_connections=config.redis.max_connections,
        decode_responses=config.redis.decode_responses,
    )

    redis_repository: BaseRedisRepository = providers.Factory(
        BaseRedisRepository,
        redis_client=redis_client,
    )

    object_storage_client: MinioObjectStorageClient = providers.Singleton(
        MinioObjectStorageClient,
        endpoint=config.minio.endpoint,
        access_key=config.minio.access_key,
        secret_key=config.minio.secret_key,
        bucket_name=config.minio.bucket_name,
        secure=config.minio.secure,
        region=config.minio.region,
        presigned_url_expire_seconds=config.minio.presigned_url_expire_seconds,
        offload_sync_calls=config.minio.offload_sync_calls,
    )

    llm: ChatOpenAI = providers.Singleton(
        ChatOpenAI,
        model_name=config.llm.model_name,
        api_key=config.llm.api_key,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        base_url=config.llm.base_url,
        extra_body=config.llm.extra_body_payload,
    )

    llm_adapter: LLMAdapter = providers.Factory(
        LLMAdapter,
        llm=llm,
    )

    langfuse_client = providers.Singleton(get_client)

    langfuse_handler = providers.Factory(CallbackHandler)
