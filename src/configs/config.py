"""Configuration module for the application."""

import os
from pathlib import Path

from omegaconf import OmegaConf
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configs.consts import _DEFAULT_CONFIG_PATH, PROJECT_ROOT

dotenv_path = Path(PROJECT_ROOT, "config", ".env")


class _BaseValidatedConfig(BaseSettings):
    """Base configuration class with validation."""

    model_config = SettingsConfigDict(
        env_file=str(dotenv_path),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="_",
    )


class LoggerConfigs(_BaseValidatedConfig):
    """Logging configuration settings."""

    logging_config_file: str = str(
        Path(PROJECT_ROOT, "config", "logging.yaml"),
    )


class PostgresDBConfigs(_BaseValidatedConfig):
    user: str = Field(alias="POSTGRES_USER")
    password: str = Field(alias="POSTGRES_PASSWORD")
    host: str = Field(alias="POSTGRES_HOST")
    port: int = Field(alias="POSTGRES_PORT")
    db: str = Field(alias="POSTGRES_DB")

    @computed_field
    @property
    def database_url(self) -> str:
        auth = f"{self.user}:{self.password}"
        location = f"{self.host}:{self.port}"

        driver = "postgresql+asyncpg"
        query_params = "async_fallback=True"

        return f"{driver}://{auth}@{location}/{self.db}?{query_params}"


class BaseDomainConfig(_BaseValidatedConfig):
    prompts_dir: Path
    recursion_limit: int


class LangGraphConfigs(_BaseValidatedConfig):
    """LangGraph configuration settings."""

    default_recursion_limit: int = Field(default=100, ge=1, description="Maximum recursion depth for graph generation.")


class LangfuseConfigs(_BaseValidatedConfig):
    base_url: str = Field(alias="LANGFUSE_BASE_URL")
    public_key: str = Field(alias="LANGFUSE_PUBLIC_KEY")
    secret_key: str = Field(alias="LANGFUSE_SECRET_KEY")


class PersonaConfig(BaseDomainConfig):
    prompts_dir: Path = Path(PROJECT_ROOT, "domains", "persona", "infrastructure", "prompt")
    recursion_limit: int = 5


class AppConfigs(_BaseValidatedConfig):
    """Application configuration settings."""

    app_host: str
    app_port: int
    logger: LoggerConfigs
    langgraph: LangGraphConfigs
    persona: PersonaConfig
    postgres: PostgresDBConfigs
    langfuse: LangfuseConfigs

    @classmethod
    def init(cls) -> "AppConfigs":
        config_path_str = os.getenv("CONFIG_PATH")
        path = Path(config_path_str) if config_path_str else _DEFAULT_CONFIG_PATH
        yaml_config = OmegaConf.to_container(OmegaConf.load(path), resolve=True)

        return cls(**yaml_config)
