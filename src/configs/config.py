"""Configuration module for the application."""

import os
from pathlib import Path

import dotenv
import yaml
from omegaconf import OmegaConf
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configs.consts import _DEFAULT_CONFIG_PATH, PROJECT_ROOT

dotenv_path = Path(PROJECT_ROOT, "config", ".env")


class _BaseValidatedConfig(BaseSettings):
    """Base configuration class with validation."""

    model_config = SettingsConfigDict(
        env_file=str(dotenv_path),
        env_file_encoding="utf-8",
        extra="forbid",
        env_nested_delimiter="_",
    )


class LoggerConfigs(_BaseValidatedConfig):
    """Logging configuration settings."""

    logging_config_file: str = str(
        Path(PROJECT_ROOT, "config", "logging.yaml"),
    )


class BaseDomainConfig(_BaseValidatedConfig):
    prompts_dir: Path
    recursion_limit: int


class LangGraphConfigs(_BaseValidatedConfig):
    """LangGraph configuration settings."""

    default_recursion_limit: int = Field(default=100, ge=1, description="Maximum recursion depth for graph generation.")


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

    @classmethod
    def init(cls) -> "AppConfigs":
        dotenv.load_dotenv(dotenv_path)
        config_path_str: str | None = os.getenv("CONFIG_PATH")
        path: Path = Path(config_path_str) if config_path_str else _DEFAULT_CONFIG_PATH
        config = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
        return cls(**config)

    def export(self, path: Path) -> None:
        """Export the current configuration to a YAML file."""
        with open(path, "w") as output_file:
            yaml.safe_dump(
                self.model_dump(),
                output_file,
                default_flow_style=False,
                sort_keys=False,
            )
