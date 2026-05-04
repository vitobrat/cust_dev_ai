"""Infrastructure service configuration classes.

Connection settings for PostgreSQL, RabbitMQ, Redis, Langfuse, and LLM.
"""

from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configs.consts import (
    MINIO_DEFAULT_PRESIGNED_URL_EXPIRE_SECONDS,
    MINIO_MAX_PRESIGNED_URL_EXPIRE_SECONDS,
    PROJECT_ROOT,
)

dotenv_path = Path(PROJECT_ROOT, "config", ".env")


class _BaseValidatedConfig(BaseSettings):
    """Base configuration class with validation and environment variable support.

    Attributes:
        model_config: Pydantic settings configuration with env file path and encoding.
    """

    model_config = SettingsConfigDict(
        env_file=str(dotenv_path),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="_",
    )


class PostgresDBConfigs(_BaseValidatedConfig):
    """PostgreSQL database configuration settings.

    Attributes:
        user: Database username from POSTGRES_USER environment variable.
        password: Database password from POSTGRES_PASSWORD environment variable.
        host: Database host from POSTGRES_HOST environment variable.
        port: Database port from POSTGRES_PORT environment variable.
        db: Database name from POSTGRES_DB environment variable.
        pool_size: Connection pool size for SQLAlchemy engine.
        max_overflow: Maximum overflow connections beyond pool_size.
        echo: Enable SQLAlchemy query logging. Defaults to False.
    """

    user: str = Field(alias="POSTGRES_USER")
    password: str = Field(alias="POSTGRES_PASSWORD")
    host: str = Field(alias="POSTGRES_HOST")
    port: int = Field(alias="POSTGRES_PORT")
    db: str = Field(alias="POSTGRES_DB")
    pool_size: int = Field(default=5, description="Number of persistent connections in the SQLAlchemy pool.")
    max_overflow: int = Field(default=10, description="Max connections allowed above pool_size before blocking.")
    echo: bool = Field(default=False, description="Log all SQL statements issued by SQLAlchemy.")

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL.

        Returns:
            Fully qualified asyncpg database URL with connection parameters.
        """
        auth = f"{self.user}:{self.password}"
        location = f"{self.host}:{self.port}"
        driver = "postgresql+asyncpg"
        query_params = "async_fallback=True"

        return f"{driver}://{auth}@{location}/{self.db}?{query_params}"


class RabbitMQConfigs(_BaseValidatedConfig):
    """RabbitMQ broker connection settings including credentials.

    Attributes:
        host: RabbitMQ server hostname.
        port: AMQP port.
        vhost: Virtual host path.
        user: Broker username (loaded from environment).
        password: Broker password (loaded from environment).
    """

    host: str
    port: int
    vhost: str
    user: str = Field(alias="RABBITMQ_USER")
    password: str = Field(alias="RABBITMQ_PASSWORD")


class RedisConfigs(_BaseValidatedConfig):
    """Redis connection configuration settings.

    Attributes:
        host: Redis server host from REDIS_HOST environment variable.
        port: Redis server port from REDIS_PORT environment variable.
        password: Redis password from REDIS_PASSWORD environment variable.
        db: Redis logical database number (0-15) from REDIS_DB environment variable.
        max_connections: Maximum number of connections in the pool.
        decode_responses: If True, decode byte responses to strings.
        timeout: Seconds to wait for a message in BRPOP.
    """

    host: str
    port: int
    password: str = Field(alias="REDIS_PASSWORD")
    db: int = Field(default=0)
    max_connections: int = Field(default=10, description="Maximum connections in the Redis pool.")
    decode_responses: bool = Field(default=True, description="Decode byte responses to strings.")
    timeout: int = Field(default=5, description="Timeout for waiting a message from redis")

    @computed_field
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL.

        Returns:
            Redis URL in format ``redis://:password@host:port/db``.
        """
        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"


class MinioConfigs(_BaseValidatedConfig):
    """Minio object storage configuration.

    Attributes:
        endpoint: Minio API endpoint without protocol, e.g. ``minio:9000``.
        access_key: Access key loaded from environment.
        secret_key: Secret key loaded from environment.
        bucket_name: Bucket used for generated report files.
        secure: Use HTTPS when connecting to Minio.
        region: Minio/S3 bucket region.
        presigned_url_expire_seconds: Default expiration for temporary download URLs.
        offload_sync_calls: Run blocking SDK calls in a threadpool when True.
    """

    endpoint: str
    access_key: str = Field(alias="MINIO_ACCESS_KEY")
    secret_key: str = Field(alias="MINIO_SECRET_KEY")
    bucket_name: str = Field(default="custdev-reports", min_length=3)
    secure: bool = False
    region: str = Field(default="us-east-1", min_length=1)
    presigned_url_expire_seconds: int = Field(
        default=MINIO_DEFAULT_PRESIGNED_URL_EXPIRE_SECONDS,
        ge=60,
        le=MINIO_MAX_PRESIGNED_URL_EXPIRE_SECONDS,
    )
    offload_sync_calls: bool = True


class LangfuseConfigs(_BaseValidatedConfig):
    """Langfuse observability platform configuration.

    Attributes:
        base_url: Langfuse API base URL from LANGFUSE_BASE_URL environment variable.
        public_key: Langfuse public key from LANGFUSE_PUBLIC_KEY environment variable.
        secret_key: Langfuse secret key from LANGFUSE_SECRET_KEY environment variable.
    """

    base_url: str = Field(alias="LANGFUSE_BASE_URL")
    public_key: str = Field(alias="LANGFUSE_PUBLIC_KEY")
    secret_key: str = Field(alias="LANGFUSE_SECRET_KEY")


class LLMConfigs(_BaseValidatedConfig):
    """LLM client configuration settings.

    Attributes:
        model_name: Name of the language model to use.
        base_url: Base URL of the LLM API endpoint.
        api_key: API key for authentication (loaded from environment).
        temperature: Sampling temperature for generation.
        max_tokens: Maximum number of tokens in a single response.
    """

    model_name: str
    base_url: str
    api_key: str = Field(alias="LLM_API_KEY")
    temperature: float
    max_tokens: int
