"""Application configuration module.

Assembles server, domain, and infrastructure configs into a single
``AppConfigs`` entry point loaded from YAML + environment variables.
"""

import os
from pathlib import Path

from omegaconf import OmegaConf
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configs.consts import (
    _DEFAULT_CONFIG_PATH,
    DEFAULT_GRAPH_RECURSION_LIMIT,
    INTERVIEW_SIMULATION_RECURSION_LIMIT,
    PROJECT_ROOT,
    LogLevels,
)
from src.configs.infrastructure_config import LangfuseConfigs as LangfuseConfigs
from src.configs.infrastructure_config import LLMConfigs as LLMConfigs
from src.configs.infrastructure_config import (
    PostgresDBConfigs as PostgresDBConfigs,
)
from src.configs.infrastructure_config import RabbitMQConfigs as RabbitMQConfigs
from src.configs.infrastructure_config import RedisConfigs as RedisConfigs
from src.configs.log.logger import get_logger

dotenv_path = Path(PROJECT_ROOT, "config", ".env")
logger = get_logger(__name__)


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


class LoggerConfigs(_BaseValidatedConfig):
    """Logging configuration settings.

    Attributes:
        logging_config_file: Path to the logging configuration YAML file.
    """

    logging_config_file: Path = Path(PROJECT_ROOT, "config", "logging.yaml")


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
            prompts_dir_value: The path provided in the configuration.

        Returns:
            The absolute path to the prompts directory.

        Raises:
            ValueError: If the path does not exist or is not a directory.
        """
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


class PersonaConfig(BaseDomainConfig):
    """Persona domain-specific configuration.

    Attributes:
        graph_recursion_limit: Maximum recursion depth for persona LangGraph agent loops.
    """

    prompts_dir: Path = Path(PROJECT_ROOT, "src", "domains", "persona", "infrastructure", "prompt")
    graph_recursion_limit: int = Field(default=5, description="Max recursion depth for LangGraph persona agent loops.")


class InterviewConfig(BaseDomainConfig):
    """Interview domain-specific configuration."""

    prompts_dir: Path = Path(PROJECT_ROOT, "src", "domains", "interview", "infrastructure", "prompt")
    recursion_limit: int = Field(default=10, ge=1, description="Max recursion depth for interview graph agents.")
    simulation_recursion_limit: int = Field(
        default=INTERVIEW_SIMULATION_RECURSION_LIMIT,
        ge=1,
        description="Max recursion depth for the simulated interview dialogue graph.",
    )


class AppConfigs(_BaseValidatedConfig):
    """Root application configuration aggregating all subsystem configs.

    This class serves as the main entry point for application configuration,
    combining server settings with domain and infrastructure configs.

    Attributes:
        app_host: Application server host address.
        app_port: Application server port number.
        log_level: Logging verbosity level.
        workers_number: Number of uvicorn worker processes.
        logger: Logging subsystem configuration.
        persona: Persona domain configuration.
        interview: Interview domain configuration.
        rabbitmq: RabbitMQ broker configuration.
        postgres: PostgreSQL database configuration.
        redis: Redis connection configuration.
        langfuse: Langfuse observability configuration.
        llm: LLM client configuration.
    """

    app_host: str
    app_port: int
    log_level: LogLevels
    workers_number: int
    logger: LoggerConfigs = Field(default_factory=LoggerConfigs)
    persona: PersonaConfig
    interview: InterviewConfig = Field(default_factory=InterviewConfig)
    rabbitmq: RabbitMQConfigs
    postgres: PostgresDBConfigs
    redis: RedisConfigs
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
