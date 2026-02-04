'''Configuration module for the application.'''

from pathlib import Path

import yaml
from omegaconf import OmegaConf
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.configs.constants import PROJECT_ROOT

dotenv_path = Path(PROJECT_ROOT, 'config', '.env')


class _BaseValidatedConfig(BaseSettings):
    """Base configuration class with validation."""

    model_config = SettingsConfigDict(
        env_file=str(dotenv_path),
        env_file_encoding='utf-8',
        extra='forbid',
        env_nested_delimiter='_',
    )


class LoggerConfigs(_BaseValidatedConfig):
    """Logging configuration settings."""

    logging_config_file: str = str(
        Path(PROJECT_ROOT, 'config', 'logging.yaml'),
    )


class LangGraphConfigs(_BaseValidatedConfig):
    """LangGraph configuration settings."""

    default_recursion_limit: int = Field(default=100, env='DEFAULT_RECURSION_LIMIT')


class AppConfigs(_BaseValidatedConfig):
    """Application configuration settings."""

    app_host: str
    app_port: int
    logger: LoggerConfigs
    langgraph: LangGraphConfigs

    @classmethod
    def from_yaml(cls, path: Path) -> 'AppConfigs':
        config = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
        return cls(**config)

    def to_yaml(self, path: Path) -> None:
        with open(path, 'w') as output_file:
            yaml.safe_dump(
                self.model_dump(),
                output_file,
                default_flow_style=False,
                sort_keys=False,
            )
