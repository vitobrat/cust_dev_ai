"""Configuration module for the application.

This module provides Pydantic-based configuration classes for managing
application settings from YAML files and environment variables. It supports
nested configurations and automatic validation.
"""

import os
from pathlib import Path

from omegaconf import OmegaConf
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configs.consts import (
    _DEFAULT_CONFIG_PATH,
    DEFAULT_GRAPH_RECURSION_LIMIT,
    PROJECT_ROOT,
    LogLevels,
)
from src.configs.log.logger import get_logger

dotenv_path = Path(PROJECT_ROOT, "config", ".env")
logger = get_logger(__name__)


class _BaseValidatedConfig(BaseSettings):
    """Base configuration class with validation and environment variable support.

    This class provides common configuration for all settings classes,
    including environment file loading and nested delimiter support.

    Attributes:
        model_config: Pydantic settings configuration with env file path and encoding.
    """

    model_config = SettingsConfigDict(
        env_file=str(dotenv_path),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="_",
    )


class LoggerConfigs(_BaseValidatedConfig):
    """Logging configuration settings.

    Attributes:
        logging_config_file: Path to the logging configuration YAML file.
    """

    logging_config_file: Path = Path(PROJECT_ROOT, "config", "logging.yaml")


class PostgresDBConfigs(_BaseValidatedConfig):
    """PostgreSQL database configuration settings.

    This class manages database connection parameters and constructs
    the async database URL for SQLAlchemy.

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


class BaseDomainConfig(_BaseValidatedConfig):
    """Base configuration for domain-specific settings.

    Attributes:
        prompts_dir: Directory path containing prompt templates.
        recursion_limit: Maximum recursion depth for graph operations.
            Defaults to DEFAULT_GRAPH_RECURSION_LIMIT.
    """

    prompts_dir: Path
    recursion_limit: int = Field(default=DEFAULT_GRAPH_RECURSION_LIMIT, ge=1)

    @field_validator("prompts_dir", mode="after")
    @classmethod
    def make_path_absolute(cls, prompts_dir_value: Path) -> Path:
        """Convert prompts_dir to an absolute path and validate its existence.

        Args:
            v: The path provided in the configuration.

        Returns:
            The absolute path to the prompts directory.

        Raises:
            ValueError: If the path does not exist or is not a directory.
        """
        # .expanduser() handles '~' and .resolve() makes it absolute
        absolute_path = prompts_dir_value.expanduser().resolve()

        if not absolute_path.exists():
            logger.error("Configured prompts_dir for persona does not exist")
            raise ValueError(f"Configured prompts_dir does not exist: '{absolute_path}'")

        if not absolute_path.is_dir():
            logger.error("Configured prompts_dir for persona is not a directory")
            raise ValueError(f"Configured prompts_dir is not a directory: '{absolute_path}'")

        return absolute_path


class LangGraphConfigs(_BaseValidatedConfig):
    """LangGraph framework configuration settings.

    Attributes:
        default_recursion_limit: Maximum recursion depth for graph generation.
            Must be at least 1. Defaults to DEFAULT_GRAPH_RECURSION_LIMIT.
    """

    default_recursion_limit: int = Field(
        default=DEFAULT_GRAPH_RECURSION_LIMIT,
        ge=1,
        description="Maximum recursion depth for graph generation.",
    )


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


class PersonaConfig(BaseDomainConfig):
    """Persona domain-specific configuration.

    Attributes:
        graph_recursion_limit: Maximum recursion depth for persona LangGraph agent loops.
    """

    graph_recursion_limit: int = Field(default=5, description="Max recursion depth for LangGraph persona agent loops.")


class LLMConfigs(_BaseValidatedConfig):
    model_name: str
    base_url: str
    api_key: str = Field(alias="LLM_API_KEY")
    temperature: float
    max_tokens: int


class AppConfigs(_BaseValidatedConfig):
    """Root application configuration aggregating all subsystem configs.

    This class serves as the main entry point for application configuration,
    combining all domain and infrastructure settings.

    Attributes:
        app_host: Application server host address.
        app_port: Application server port number.
        logger: Logging subsystem configuration.
        langgraph: LangGraph framework configuration.
        persona: Persona domain configuration.
        postgres: PostgreSQL database configuration.
        langfuse: Langfuse observability configuration.
    """

    app_host: str
    app_port: int
    log_level: LogLevels
    workers_number: int
    logger: LoggerConfigs = Field(default_factory=LoggerConfigs)
    persona: PersonaConfig
    rabbitmq: RabbitMQConfigs
    postgres: PostgresDBConfigs
    langfuse: LangfuseConfigs
    llm: LLMConfigs

    @classmethod
    def init(cls) -> "AppConfigs":
        """Initialize application configuration from YAML file.

        Loads configuration from YAML file specified by CONFIG_PATH environment
        variable, or uses default path if not set. Resolves OmegaConf interpolations
        and validates all settings.

        Returns:
            Fully initialized and validated AppConfigs instance.

        Raises:
            ValidationError: If configuration values fail Pydantic validation.
            FileNotFoundError: If configuration file does not exist.
        """
        config_path_str = os.getenv("CONFIG_PATH")
        path = Path(config_path_str) if config_path_str else _DEFAULT_CONFIG_PATH
        yaml_config = OmegaConf.to_container(OmegaConf.load(path), resolve=True)

        return cls(**yaml_config)
