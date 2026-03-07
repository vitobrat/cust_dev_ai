"""Configuration module for the application.

This module provides Pydantic-based configuration classes for managing
application settings from YAML files and environment variables. It supports
nested configurations and automatic validation.
"""

import os
from pathlib import Path

from omegaconf import OmegaConf
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configs.consts import _DEFAULT_CONFIG_PATH, PROJECT_ROOT

dotenv_path = Path(PROJECT_ROOT, "config", ".env")


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

    logging_config_file: str = str(
        Path(PROJECT_ROOT, "config", "logging.yaml"),
    )


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
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

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


class BaseDomainConfig(_BaseValidatedConfig):
    """Base configuration for domain-specific settings.

    Attributes:
        prompts_dir: Directory path containing prompt templates.
        recursion_limit: Maximum recursion depth for graph operations.
    """

    prompts_dir: Path
    recursion_limit: int


class LangGraphConfigs(_BaseValidatedConfig):
    """LangGraph framework configuration settings.

    Attributes:
        default_recursion_limit: Maximum recursion depth for graph generation.
            Must be at least 1. Defaults to 100.
    """

    default_recursion_limit: int = Field(
        default=100,
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
        prompts_dir: Directory containing persona generation prompt templates.
        recursion_limit: Maximum recursion depth for persona generation graphs.
            Defaults to 5.
    """

    prompts_dir: Path = Path(PROJECT_ROOT, "domains", "persona", "infrastructure", "prompt")
    recursion_limit: int = 5


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
    logger: LoggerConfigs
    langgraph: LangGraphConfigs
    persona: PersonaConfig
    postgres: PostgresDBConfigs
    langfuse: LangfuseConfigs

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
